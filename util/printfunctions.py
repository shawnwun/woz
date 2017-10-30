######################################################################
######################################################################
#  Copyright Tsung-Hsien Wen, Cambridge Dialogue Systems Group, 2017 #
######################################################################
######################################################################

#! /usr/bin/python
# -*- coding: utf-8 -*-

__author__="Shawn Wen"
__date__ ="$16-Mar-2017 16:57:34$"

import xml.dom.minidom
import re
import os
import random
from xml.dom.minidom import Node
import json

import cgi
import cgitb
cgitb.enable()

import sys
if '' not in sys.path:
    sys.path.append('')
from utils import *
from lockfile import LockFile
import json

#######################################
############ User Side ################
#######################################
def printUserSteps():
    print '<p>This HIT requires you to role play <span class="emphasis">a help desk client</span> and carry on a conversation with a help desk clerk.</p>'
    print '<b>The task:</b><ul style="line-height:120%%">'
    scenario = [    
        'You are texting to an help desk clerk asking for help.',
        'You need to play your role based on the script defined in the task box at the bottom right.',
        'You only need to key-in <span class="emphasis">one appropriate response</span> given the current dialogue scenario.'
    ]
    print '\n'.join(['<li>'+x+'</li>'for x in scenario])+'</ul>'
    print '<b>The steps</b> to follow:<ol style="line-height:120%">'
    steps = [
        'Go through the dialogue history by clicking the <i>"next turn"</i> button.',
        'Type in an appropriate sentence to proceed the dialogue.'
    ]
    print '\n'.join(['<li>'+x+'</li>'for x in steps])+'</ol>'
    print '<b>The hints:</b><ul style="line-height:120%">'
    hints = [
        'Your response is limited to a <span class="emphasis">maximum number of 30 words</span>. There is a count down helper at the bottom right corner of the text field.',
        'Ask for the relevant information as given in the task box (e.g. search restaurant by food type, book a hotel, buy a train ticket ... etc).',        
        '<b class="emphasis">Don\'t put everything in a single request.</b> Divide them naturally into several turns if necessary.',
        'If the help desk clerk asks about something that is not in the task, say you don\'t care or something similar.',
        'Ask for the the attributes as given in the task box (e.g. <i>"You want to know the address of the restaurant"</i>).',
        'If you have got all the information specified in the task box, simply type a goodbye message to end the dialogue.',
        'Otherwise, just chat naturally to the clerk!',
    ]
    print '\n'.join(['<li>'+x+'</li>'for x in hints])+'</ul>'


#######################################
########### System Side ###############
#######################################

###############################################################################################
###############################################################################################
###############################################################################################
slots = {
    'restaurant':   ['name','food','area','pricerange','phone','postcode','address'],
    'hotel':        ['name','type','area','pricerange','stars','internet','parking',
                    'phone','postcode','address'],
    'attraction':   ['name','type','area','phone','postcode','address','entrance fee'],
    'hospital':     ['department','phone'],
    'taxi':         ['departure','destination','leaveAt','arriveBy'],
    'train':        ['trainID','departure','destination','day','leaveAt','arriveBy','price','duration'],
    'police':       []
}

booking_slots = {
    'restaurant':   ['day','time','people'],
    'hotel':        ['day','stay','people'],
    'attraction':   [],
    'hospital':     [],
    'taxi':         [],
    'police':       [],
    'train':        ['people']
}

sortIndex = {
    'restaurant':   1,
    'hotel':        1,
    'attraction':   1,
    'hospital':     0,
    'taxi':         0,
    'police':       0,
    'train':        3,
}

surfaceForms = {
    'name':'Name', 'food':'Food Type', 'area':'Area', 'pricerange':'Price Range',
    'phone':'Phone', 'postcode':'Postcode', 'address':'Address', 'stars':'Star',
    'parking':'Parking', 'internet':'Internet', 'type':'Type', 
    'entrance fee':'Entrance Fee', 'department':'Department'
}
pois = set(['addenbrookes hospital','parkside police station'])

hours = ['0'+str(i) for i in range(5,10)] + [str(i) for i in range(10,25)]
openingHours = [str(i) for i in range(10,21)]
hours24 = ['0'+str(i) for i in range(1,10)] + [str(i) for i in range(10,25)]
mins_quater = ['00','15','30','45']

timeNormal = []
for h in hours:
    for m in mins_quater:
        timeNormal.append(h+':'+m)
trainTime = ['not mentioned'] + timeNormal

taxiTime = ['not mentioned']
for h in hours24:
    for m in mins_quater:
        taxiTime.append(h+':'+m)

timeWork = []
for h in openingHours:
    for m in mins_quater:
        timeWork.append(h+':'+m)
timeWork.append('21:00')

week = ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']

booking = {
    'restaurant':   ['day','time','people'],
    'hotel':        ['day','stay','people']
}

stays = [str(i) for i in range(1,9)]
ppl   = [str(i) for i in range(1,9)]

###############################################################################################
###############################################################################################
###############################################################################################

def printDefaultSuggestedValues():
    print "<script>var default_sources = ["
    suggesttexts = []
    for s in [ppl,stays,week,timeNormal,timeWork]:
        suggesttexts.append('['+','.join(['\"'+x+'\"'for x in s])+']')
    print ','.join(suggesttexts) + '];'
    print """
    function genRef(){
        var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        var ref = "";
        for( var i=0; i < 8; i++ )
            ref += possible.charAt(Math.floor(Math.random() * possible.length));
        return ref;
    }
    function genTime(){
        var times = ["9:00","10:00","11:00","12:00","13:00","14:00","15:00","16:00"];
        var days  = ["Monday","Tuesday","Wednesday","Thursday","Friday"];
        var time  = times[Math.floor(Math.random()*times.length)];
        var day   = days[Math.floor(Math.random()*days.length)];
        return [time, day]
    }
    function getMethods(obj) {
        var result = [];
        for (var id in obj) {
            try {
                if (typeof(obj[id]) == "function") {
                    result.push(id + ": " + obj[id].toString());
                }
            } catch (err) {
                result.push(id + ": inaccessible");
            }
        }
        return result;
    }
    </script>"""


def loadDOM(domain):
   
    # loading db and s2v files
    fin = file('ontology/'+domain+'_db.json')
    db = json.load(fin)
    fin.close()
    fin = file('ontology/'+domain+'_s2v.json')
    s2v = json.load(fin)
    fin.close()    
    # accumulate informable slot values from both file and db
    for e in db:
        for s in slots[domain]:
            if e.has_key(s) and s2v.has_key(s):
                s2v[s].append(e[s])
    # adding requestable slots
    for s in slots[domain]:
        if not s2v.has_key(s): s2v[s] = []
    # add special values to s2v
    for s,vs in s2v.iteritems():
        if len(vs)!=0:
            if s=='departure' or s=='destination':
                s2v[s] = ['not mentioned'] + sorted(list(set(vs)))
            else:
                s2v[s] = ['not mentioned','dont care'] + sorted(list(set(vs)))

    # adding POIs
    if domain=='restaurant' or domain=='hotel' or domain=='attraction' or domain=='train':
        for e in db:
            for s in slots[domain]:
                if s=='name':
                    pois.add(e[s])
                if s=='departure':
                    pois.add(e[s]+' train station')

    return db, s2v

def printSysSteps():
    print '<p>This HIT requires you to <span class="emphasis">role play a help desk clerk</span> and carry on a conversation with a help desk client.</p>'
    print '<b>The task:</b><ul style="line-height:120%%">'
    scenario = [
        'Your task is to provide information and help for residents or tourists in the <span class="emphasis">Cambridge, UK area</span>.',
        'You are texting to a client to provide your service.',
        'You are given a console below to help you look for relevant information, therefore <span class="emphasis">this console also defines the set of tasks</span> that you can help with.',
        'You only need to key-in <span class="emphasis">one appropriate response</span> given the current dialogue scenario.'
    ]
    print '\n'.join(['<li>'+x+'</li>'for x in scenario])+'</ul>'
    print '<b>The domains</b> you can help with:<ol style="line-height:120%">'
    scenes= [
        'find or book a restaurant',
        'find or book a hotel',
        'find, call, or book a hospital department',
        'find or call a police station',
        'find or suggest a tourist attraction in town',
        'find or book a train ticket',
        'book a taxi'
    ]
    print '\n'.join(['<li>'+x+'</li>'for x in scenes])+'</ol>'
    print '<b>The steps</b> to follow:<ol style="line-height:120%">'
    steps = [
        'Go through the dialogue history by clicking the <i>"next turn"</i> button.',
        'Choose the appropriate domain to work on based on the dialogue context.<br>Sometimes the task may require information from several domains.',
        'Update the questionnaires inside the domain tab. <ul><li>Fill in <i>"not mentioned"</i> when the attribute is not mentioned.</li><li>Fill in <i>"dont care"</i> when the attribute doesn\'t matter to the customer.</li><li>Otherwise, choose one of the category from the suggested list</li></ul>',
        'Type in an appropriate response, either: <ul><li>Ask for more constraints.</li><li>Make a recommendation.</li><li>Answer questions.</li><li>Summarise database information</li><li>Normal chat. (e.g. thank you goodbye, you\'re welcome ... etc)</li></ul>Note, your response is limited to a <span class="emphasis">maximum number of 40 words</span>.',
        'If your client is satisfied, type in a goodbye message and tick the <i>"end-of-dialogue"</i> box.<br><b class="emphasis">DO NOT tick it if the dialogue is not supposed to end.</b>'
    ]
    print '\n'.join(['<li>'+x+'</li>'for x in steps])+'</ol>'


def printTab():
    print """
    <div class="tab" id="domainTab">
      <button class="tablinks" onclick="openDomain(event, 'restaurant')" disabled>Restaurant</button>
      <button class="tablinks" onclick="openDomain(event, 'hotel')" disabled>Hotel</button>
      <button class="tablinks" onclick="openDomain(event, 'attraction')" disabled>Attraction</button>
      <button class="tablinks" onclick="openDomain(event, 'hospital')" disabled>Hospital</button>
      <button class="tablinks" onclick="openDomain(event, 'police')" disabled>Police</button>
      <button class="tablinks" onclick="openDomain(event, 'train')" disabled>Train</button>
      <button class="tablinks" onclick="openDomain(event, 'taxi')" disabled>Taxi</button>
      <defaultButton class="tablinks" onclick="openDomain(event, 'default')" id='defaultButton' ></button>
    </div>
    <script>
    
    // Get the element with id="defaultOpen" and click on it
    function openDomain(evt, domain) {
        
        // Declare all variables
        var i, tabbackground, tablinks;
        // Get all elements with class="tabcontent" and hide them
        tabbackground = document.getElementsByClassName("tabbackground");
        for (i = 0; i <tabbackground.length; i++) {
            tabbackground[i].style.display = "none";
        }
        // Get all elements with class="tablinks" and remove the class "active"
        tablinks = document.getElementsByClassName("tablinks");
        for (i = 0; i < tablinks.length; i++) {
            tablinks[i].className = tablinks[i].className.replace(" active", "");
        }
        // Show the current tab, and add an "active" class to the button that opened the tab
        document.getElementById(domain).style.display = "block";
        evt.currentTarget.className += " active";
        // make the informable slots at this domain required
        $('.semiq').each(function (){
            if ($(this).is(':hidden')){
            } else{
                $(this).prop('required',true);
            }
        });

        if (domain=="taxi"){
            taxiBookInit();
        }

        // find the corresponding row and open row child
        var searchSlot= "name";
        if (domain=='restaurant'){}
        else if (domain=='hotel'){}
        else if (domain=='hospital'){
            searchSlot = "department";
        } else if (domain=='train'){
            searchSlot = "trainID";
        } else { return true;}

        table = $('#'+domain+'Table').dataTable();
        if ($('#'+domain+'Table').is(":visible")){
            unlockResponse(animate=false);
        }
        if (window[domain+'_book']['booked'].length==0) var rowId = ""
        else var rowId = table.fnFindCellRowIndexes(window[domain+'_book']['booked'][0][searchSlot], 0);
        if (rowId!=""){
            // get row and its corresponding node
            var row = $('#'+domain+'Table').DataTable().row( rowId );
            var tr = row.node();
            // Open this row child
            if ( $('#'+domain+'Table').DataTable().row( '.shown' ).length ) {
                $('.details-control', $('#'+domain+'Table').DataTable().row( '.shown' ).node()).click();
            }
            row.child( window[domain+'Format'](row.data()) ).show();
            $(tr).addClass('shown');
            window[domain+'BookSuggestion']();
            // prevent default submit for booking button
            $("#book_"+domain+"_questions").submit(function(e){
                e.preventDefault();
                window[domain+'BookConfirmation']();
                return false;
            });
            // init booking query and scroll down
            window[domain+'BookInit']();
            var h = $("#"+domain+"Table").offset().top;
            $("html, body").animate({ scrollTop: h }, 500);
        }
    }
    </script>"""

def printSuggestionAndHistory(slots,s2v,metadata,domain):
    # print suggested source
    print "var %s_sources = [" % domain
    suggesttexts = []
    for s in slots:
        suggesttexts.append('['+','.join(['\"'+x+'\"'for x in s2v[s]])+']')
    print ','.join(suggesttexts) + '];'
    # print semi history
    if 'semi' in metadata:
        print 'var %s_semi = %s;' % (domain,json.dumps(metadata['semi']))
    else:
        print 'var %s_semi = {};' % (domain)
    # print book history
    if 'book' in metadata:
        print 'var %s_book = %s;' % (domain,json.dumps(metadata['book']))
    else:
        print 'var %s_book = {};' % (domain)
    # print domain slots
    print 'var %s_slots= %s;' % (domain,json.dumps(slots))

def loadDatasets():

    DB = {}
    S2V= {}
    for domain in ['restaurant','hotel','attraction','hospital','train','taxi']:
        db,s2v = loadDOM(domain)
        DB[domain] = db
        S2V[domain]= s2v
        if domain=='train':
            s2v['arriveBy']= trainTime
            s2v['leaveAt'] = trainTime
            s2v['day'] = ['not mentioned'] + week
        elif domain=='taxi':
            s2v['arriveBy']= taxiTime
            s2v['leaveAt'] = taxiTime
            s2v['destination'] = ['not mentioned'] + sorted(list(pois))
            s2v['departure'] = ['not mentioned'] + sorted(list(pois))
    DB['police'] = []
    S2V['police'] = []
    return DB, S2V

def printMetadata(metadata,s2v):

    print "<script>"
    for domain in metadata.iterkeys():
        printSuggestionAndHistory(slots[domain],s2v[domain],metadata[domain],domain)
    print "</script>"

def printRestaurantTab(metadata,db,s2v):
    # create valid widget ids based on informable slots
    ids = []
    for i in range(len(slots['restaurant'])):
        if len(s2v[slots['restaurant'][i]])!=0: ids.append(str(i))
    print """
    <div id="restaurant" class="tabbackground"> 
    <div class="questionnaire">
        <form id="restaurant_questions">
        <p>Please <b>modifiy</b> the following answers based on the latest customer response:</p>
        <li>What does the user want?</li>
        <table id="restaurant_informable">
            <tbody><tr>
                <td>Is the user looking for a specific restaurant <b>by name</b>?</td>
                <td><input class="semiq" id="%s" type="text" name="name" placeholder="choose"/></td>
            </tr>
            <tr>
                <td>What is the <b>food type</b> the user wants?</td>
                <td><input class="semiq" id="%s" type="text" name="food" placeholder="choose"/></td>
            </tr>
            <tr>
                <td>What is the <b>area</b> the user wants?</td>
                <td><input class="semiq" id="%s" type="text" name="area" placeholder="choose"/></td>
            </tr>
            <tr>
                <td>What is the <b>price range</b> the user wants?</td>
                <td><input class="semiq" id="%s" type="text" name="pricerange" placeholder="choose"/></td>
            </tr></tbody>
        </table>
        <input id="restaurant_search" type="submit" class="button lookup" value="Lookup">
        </form>
    </div>
    """ % tuple(['restaurant_informable'+id for id in ids])

    #printSuggestionAndHistory(slots['restaurant'],s2v,metadata,'restaurant')
    printTable(db,slots['restaurant'],'restaurant',metadata)
    printTableScript('restaurant',metadata) 

def printHotelTab(metadata,db,s2v):
    # create valid widget ids based on informable slots
    ids = []
    for i in range(len(slots['hotel'])):
        if len(s2v[slots['hotel'][i]])!=0: ids.append(str(i))
    print """
    <div id="hotel" class="tabbackground"> 
    <div class="questionnaire">
        <form id="hotel_questions">
        <p>Please <b>modifiy</b> the following answers based on the latest customer response:</p>
        <li>What does the user want?</li>
        <table id="hotel_informable">
            <tbody><tr>
                <td>Is the user looking for a specific hotel <b>by name</b>?</td>
                <td><input class="semiq" id="%s" type="text" name="name" placeholder="choose"/></td>
            </tr>
            <tr>
                <td>What is the <b>hotel type</b> the user wants?</td>
                <td><input class="semiq" id="%s" type="text" name="type" placeholder="choose"/></td>
            </tr>
            <tr>
                <td>What is the <b>area</b> the user wants?</td>
                <td><input class="semiq" id="%s" type="text" name="area" placeholder="choose"/></td>
            </tr>
            <tr>
                <td>What is the <b>price range</b> the user wants?</td>
                <td><input class="semiq" id="%s" type="text" name="pricerange" placeholder="choose"/></td>
            </tr>
            <tr>
                <td>What is the <b>star of the hotel</b> the user wants?</td>
                <td><input class="semiq" id="%s" type="text" name="stars" placeholder="choose"/></td>
            </tr>
            <tr>
                <td>Does the user need <b>internet</b> ?</td>
                <td><input class="semiq" id="%s" type="text" name="internet" placeholder="choose"/></td>
            </tr>
            <tr>
                <td>Does the user need <b>parking</b> ?</td>
                <td><input class="semiq" id="%s" type="text" name="parking" placeholder="choose"/></td>
            </tr></tbody>
        </table>
        <input id="hotel_search" type="submit" class="button lookup" value="Lookup">
        </form>
    </div>""" % tuple(['hotel_informable'+id for id in ids])

    printTable(db,slots['hotel'],'hotel',metadata)
    printTableScript('hotel',metadata) 


def printHospitalTab(metadata,db,s2v):
    print """
    <div id="hospital" class="tabbackground"> 
    <div class="questionnaire">
        <h3>Addenbrookes Hospital</h3>
        <table class="infotable"><tbody>
            <tr><td class="infotable">Telephone</td><td class="infotable">:</td><td class="infotable">01223245151</td></tr>
            <tr><td class="infotable">Address  </td><td class="infotable">:</td><td class="infotable">Hills Rd, Cambridge</td></tr>
            <tr><td class="infotable">Postcode </td><td class="infotable">:</td><td class="infotable">CB20QQ</td></tr>
        </tbody></table>

        <form id="hospital_questions">
        
        <p>Please <b>modifiy</b> the following answers based on the latest customer response:</p>
        Is the user looking for a particular <b>department</b> ?
        <input class="semiq" id="hospital_informable0" type="text" name="department" placeholder="choose"/>
        <p></p>
        <input id="hospital_search" type="submit" class="button lookup" value="Lookup">
        </form>
    </div>
    """
    printTable(db,slots['hospital'],'hospital',metadata)
    printTableScript('hospital',metadata)


def printPoliceTab(metadata):
    print """
    <div id="police" class="tabbackground"> 
    <div class="questionnaire">
        <h3>Parkside Police Station</h3>
        <table class="infotable"><tbody>
            <tr><td class="infotable">Telephone</td><td class="infotable">:</td><td class="infotable">01223358966</td></tr>
            <tr><td class="infotable">Address  </td><td class="infotable">:</td><td class="infotable">Parkside, Cambridge</td></tr>
            <tr><td class="infotable">Postcode </td><td class="infotable">:</td><td class="infotable">CB11JG</td></tr>
        </tbody></table>
        <p></p>
        <form id="police_questions">
        <input id="police_search" type="submit" class="button lookup" value="Start Replying">
        </form>
    </div>
    </div>
    <script type="text/javascript" class="init">
    $(document).ready(function() {
        // prevent submit button 
        $("#police_questions").submit(function(e){
            e.preventDefault();
            policeReady();
            return false;
        });
    });
    function policeReady(){
        unlockResponse(); 
        swal({
            title:  "Info!",
            html:   "You can type in your response now!",
            type:   "info",
            confirmButtonColor: '#2B9DAB'
        }).catch(swal.noop);
    }
    </script>
    """
def printAttactionTab(metadata,db,s2v):
    # create valid widget ids based on informable slots
    ids = []
    for i in range(len(slots['attraction'])):
        if len(s2v[slots['attraction'][i]])!=0: ids.append(str(i))
    print """
    <div id="attraction" class="tabbackground"> 
    <div class="questionnaire">
        <form id="attraction_questions">
        <p>Please <b>modifiy</b> the following answers based on the latest customer response:</p>
        <li>What does the user want?</li>
        <table id="attraction_informable">
            <tbody><tr>
                <td>Is the user looking for a specific attraction <b>by name</b>?</td>
                <td><input class="semiq" id="%s" type="text" name="name" placeholder="choose"/></td>
            </tr>
            <tr>
                <td>What is the <b>attraction type</b> the user wants?</td>
                <td><input class="semiq" id="%s" type="text" name="type" placeholder="choose"/></td>
            </tr>
            <tr>
                <td>What is the <b>area</b> the user wants?</td>
                <td><input class="semiq" id="%s" type="text" name="area" placeholder="choose"/></td>
            </tr></tbody>
        </table>
        <input id="attraction_search" type="submit" class="button lookup" value="Lookup">
        </form>
    </div>
    """ % tuple(['attraction_informable'+id for id in ids])

    printTable(db,slots['attraction'],'attraction',metadata)
    printTableScript('attraction',metadata) 


def printTaxiTab( metadata,db,s2v ):
    # create valid widget ids based on informable slots
    ids = ['0','1','2','3']
    print """
    <div id="taxi" class="tabbackground"> 
    <div class="questionnaire">
        <form id="taxi_questions">
        <p>Please <b>modifiy</b> the following answers based on the latest customer response:</p>
        <li>What does the user want?</li>
        <table id="taxi_informable">
            <tbody><tr>
                <td>Where is the <b>departure site</b> ?</td>
                <td><input class="semiq" id="%s" type="text" name="departure" placeholder="choose"/></td>
            </tr>
            <tr>
                <td>Where is the <b>destination</b> ?</td>
                <td><input class="semiq" id="%s" type="text" name="destination" placeholder="choose"/></td>
            </tr>
            <tr>
                <td>When does the user want to <b>leave</b> ?</td>
                <td><input class="semiq" id="%s" type="text" name="leaveAt" placeholder="choose"/></td>
            </tr>
            <tr>
                <td>When does the user want to <b>arrive by</b> ?</td>
                <td><input class="semiq" id="%s" type="text" name="arriveBy" placeholder="choose"/></td>
            </tr>
            </tbody>
        </table>
        <input id="taxi_search" type="submit" class="button lookup" value="Book">
        </form>
        
        <table class="infotable" id="taxi_booked_table" hidden>
            <tbody>
                <tr><td class="infotable">Booking completed!</td></tr>
                <tr><td class="infotable">Booked car type</td><td class="infotable">:</td><td id="taxi_type" class="infotable"></td></tr>
                <tr><td class="infotable">Contact number</td><td class="infotable">:</td><td id="taxi_phone" class="infotable"></td></tr>
            </tbody>
        </table>
    </div>
    """ % tuple(['taxi_informable'+id for id in ids])

    printTaxiScript()
    print '</div>'
  
def printTrainTab( metadata,db,s2v ):
    # create valid widget ids based on informable slots
    ids = ['1','2','3','4','5']
    print """
    <div id="train" class="tabbackground"> 
    <div class="questionnaire">
        <form id="train_questions">
        <p>Please <b>modifiy</b> the following answers based on the latest customer response:</p>
        <li>What does the user want?</li>
        <table id="train_informable">
            <tbody><tr>
                <td>Where is the <b>departure site</b> ?</td>
                <td><input class="semiq" id="%s" type="text" name="departure" placeholder="choose"/></td>
            </tr>
            <tr>
                <td>Where is the <b>destination</b> ?</td>
                <td><input class="semiq" id="%s" type="text" name="destination" placeholder="choose"/></td>
            </tr>
            <tr>
                <td>What <b>day</b> does the user want to travel ?</td>
                <td><input class="semiq" id="%s" type="text" name="day" placeholder="choose"/></td>
            </tr>
            <tr>
                <td>When does the user want to <b>leave</b> ?</td>
                <td><input class="semiq" id="%s" type="text" name="leaveAt" placeholder="choose"/></td>
            </tr>
            <tr>
                <td>When does the user want to <b>arrive by</b> ?</td>
                <td><input class="semiq" id="%s" type="text" name="arriveBy" placeholder="choose"/></td>
            </tr>
            </tbody>
        </table>
        <input id="train_search" type="submit" class="button lookup" value="Lookup">
        </form>
    </div>
    """ % tuple(['train_informable'+id for id in ids])

    printTable(db,slots['train'],'train',metadata)
    printTableScript('train',metadata)
  
def printDefaultTab():
    print """
    <div id="default" class="tabbackground"> 
    <div class="questionnaire">
        <center>Choose one of the domain tabs above to begin</center>
    </div>
    </div>
    """

def printTable(db,slots,domain,metadata):
   
    # show table or not based on booking status
    isBooking = False
    for slot in booking_slots[domain]:
        if 'book' in metadata and slot in metadata['book'] and metadata['book'][slot]!="":
            isBooking = True
    tableHidden = 'hidden' if not isBooking else ''
    # special case for hospital
    if domain=='hospital' and 'department' in metadata['semi'] and metadata['semi']['department']!="" and \
            metadata['semi']['department']!="not mentioned":
        tableHidden = ''

    print """
    <div class=searchtable id="{0}TableBackground" {1}>
        <table id="{2}Table" class="display" cellspacing="0" width="100%">""".format(domain,tableHidden,domain)
    print '\t\t<thead>\n\t\t\t<tr>'
    for s in slots:
        print '\t\t\t\t<th>%s</th>' % s
    if domain in ['restaurant','hotel','hospital','train']:
        print '\t\t\t\t<th>book<br>(optional)</th>'
    print '\t\t\t</tr>\n\t\t</thead>'
    print '\t\t<tfoot>\n\t\t\t<tr>'
    for s in slots:
        print '\t\t\t\t<th>%s</th>' % s
    if domain in ['restaurant','hotel','hospital','train']:
        print '\t\t\t\t<th>action</th>'
    print '\t\t\t</tr>\n\t\t</tfoot>'
    print '\t\t<tbody>'
    
    for e in db:
        print '\t\t\t<tr>'
        for s in slots:
            if e.has_key(s):    
                if s=='price':
                    print '\t\t\t\t<td style="max-width:1000px">%s</td>' % e[s]
                else:
                    print '\t\t\t\t<td style="max-width:1000px">%s</td>' % e[s]
            else:               print '\t\t\t\t<td>--</td>'
        # print reserve button
        if domain in ['restaurant','hotel','hospital','train']:
            print '\t\t\t\t<td></td>'
        print '\t\t\t</tr>'
    print"""\t\t</tbody></table>
    </div>
    </div>
    """

def printImportedScript():
    print """ 
    <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.10.11/css/jquery.dataTables.min.css">
    <style type="text/css" class="init">
        tfoot input {
            width: 100%;
            padding: 3px;
            box-sizing: border-box;}
    </style>
    <script type="text/javascript" language="javascript" src="util/jquery.dataTables.min.js"></script>
    <script type="text/javascript" src="util/fnFindCellRowIndexes.js"></script>
    <script src="https://code.jquery.com/ui/1.10.3/jquery-ui.js"></script>
    <link rel="stylesheet" href="https://code.jquery.com/ui/1.10.3/themes/smoothness/jquery-ui.css"/>
    """

def printTableScript(domain,metadata):

    isBooking = False
    for slot in booking_slots[domain]:
        if 'book' in metadata and slot in metadata['book'] and metadata['book'][slot]!="":
            isBooking = True
  
    print """
    <script type="text/javascript" class="init">
    $(document).ready(function() {
        // prevent submit button 
        $("#%s_questions").submit(function(e){
            e.preventDefault();
            %sSearchDB();
            return false;
        });

        // Setup - add a text input to each footer cell
        var count = 0;
        $('#%sTable tfoot th').each( function () {
            $(this).html( '<input id="%s_foot'+count.toString()+
                '" placeholder="nil" hidden>' );
            $( "#%s_informable"+count.toString() ).autocomplete({
                minLength:0,
                source: %s_sources[count],
                messages: {
                    noResults: '',
                    results: function() {}
                },
                select: function(event, ui) {
                    $(this).val(ui.item.value);
                    $(this).trigger('change');
                }
            });
            $( "#%s_informable"+count.toString() ).autocomplete("widget").attr('style', 'max-height: 200px; overflow-y: auto; overflow-x: hidden;')
            $( "#%s_informable"+count.toString() ).focus(function() {
                $(this).autocomplete('search', $(this).val())
            });
            count += 1;
        });"""% tuple([domain]*8)
    if domain in ['restaurant','hotel','hospital','train']:
        slot = 'name'
        if domain=='hospital':  
            slot = 'department'
        if domain=='train':     
            slot = 'trainID'

        print """
        // DataTable
        var table = $('#%sTable').DataTable({
            "lengthChange": false,
            "dom":"ltipr",
            "pageLength":5,
            "columns": [
        """% tuple([domain])
        for s in slots[domain]:
            print '\t\t\t\t{ "data": "%s" },'%s
        print """
                {   
                    "className": "details-control",
                    "orderable": false,
                    "data": null,
                    "defaultContent": ""
                }
            ],
            "order": [[%d, 'asc']]
        });""" % sortIndex[domain]
        
        print """
        // Add event listener for opening and closing details
        $('#%sTable tbody').on('click', 'td.details-control', function () {
            var tr = $(this).closest('tr');
            var row = table.row( tr );
     
            if ( row.child.isShown() ) {
                // This row is already open - close it
                row.child.hide();
                tr.removeClass('shown');
            }
            else {
                if ( table.row( '.shown' ).length ) {
                    $('.details-control', table.row( '.shown' ).node()).click();
                }
                // Open this row
                row.child( %sFormat(row.data()) ).show();
                tr.addClass('shown');
                %sBookSuggestion();
                %sBookInit();
            }
            // prevent default submit
            $("#book_%s_questions").submit(function(e){
                e.preventDefault();
                %sBookConfirmation();
                return false;
            });
        });"""% tuple([domain]*6)
    else:
        print """
        // DataTable
        var table = $('#%sTable').DataTable({
            "lengthChange": false,
            "dom":"ltipr",
            "pageLength":5,
            "order": [[%d, 'asc']]
        });"""% tuple([domain,sortIndex[domain]])

    print"""
        // Apply the search
        table.columns().every( function () {
            var that = this;
            $( 'input', this.footer() ).on( 'keyup change', function () {
                if (this.id=='train_foot4'||this.id=='train_foot5'){
                    that.draw();
                }
                else if ( that.search() !== this.value ) {
                    that.search( this.value ).draw();
                }  
            });
        } );
        // init answer informable values
        %sInitSearchVal();
    } );"""% tuple([domain])
    
    if domain=='train':
        print """
        $.fn.dataTable.ext.search.push(
            function( settings, data, dataIndex ) {
                if (settings.nTable.id=="trainTable"){
                    var inputLeave = $("#train_foot4").val();
                    var inputArrive= $("#train_foot5").val();
                    var dataLeave  = data[4];
                    var dataArrive = data[5];
                    
                    var show = true;
                    if(inputLeave!="" && dataLeave<inputLeave){
                        show = false;
                    }
                    if(inputArrive!=""&& dataArrive>inputArrive){
                        show = false;
                    }
                    return show;
                }
                else{
                    return true;
                }
            }
        )
        """

    printBookingDetails(domain,metadata)
    
    print"""
    function %sInitSearchVal(){
        for(var i=0;i<%s_slots.length;i++){
            // find answer carrier
            var infoID = "%s_informable"+i.toString()
            var infoQuery = document.getElementById(infoID);
            // initialise input textfield queries
            if(infoQuery!=null){
                if (%s_slots[i]==infoQuery.name){
                    infoQuery.value = %s_semi[%s_slots[i]]; 
                }
            }
            else {continue}
            // find search bar
            var footID = "%s_foot"+i.toString()
            var footQuery = document.getElementById(footID);
            // initialise foot search bar value and search
            if(infoQuery!=null && footQuery!=null){
                if(infoQuery.value!="dont care" && infoQuery.value!="not mentioned"){
                    footQuery.value = infoQuery.value
                } else{
                    footQuery.value = '';
                }
                var event = new Event('change');
                footQuery.dispatchEvent(event);
            }
        }
    }
    function %sSearchDB(){
        // check whether the domain aligns to goal
        if (size_dict(goal["%s"])==0){
            
            swal({
                title:  "Error!",
                html:   "It seems like you are choosing the wrong domain to work on.",
                type:   "error",
                confirmButtonColor: '#2B9DAB'
            }).catch(swal.noop);
 
            return false;
        }""" %  tuple([domain]*9)
    if False: 
        print """
        // check whether the slot value pairs aligns to goal
        var isMatch = true;
        for(var i=0;i<%s_slots.length;i++){
            var infoQuery = document.getElementById("%s_informable"+i.toString());
            if(infoQuery!=null){
                var s = %s_slots[i];
                var v = infoQuery.value;
                var slotMatch = false;
                if (v=='not mentioned' || v=='dont care'){
                    // if value is not mentioned or dontcare, approve it
                    slotMatch = true;
                } else if (s in goal["%s"]["info"] || s in goal["%s"]["fail_info"]){
                    if (s in goal["%s"]["info"] && v==goal["%s"]["info"][s]) slotMatch = true
                    if (s in goal["%s"]["fail_info"] && v==goal["%s"]["fail_info"][s]) slotMatch = true
                } else {
                    // slot not specified in goal, should not allocate it value
                    slotMatch = false;
                }
                // for every slot it needs match
                isMatch = isMatch && slotMatch;
            }
        } if (!isMatch){
            swal({
                title:  "Error!",
                html:   "This occurs either:<br>1. You are not interpreting the semantics correctly, or<br>2. The user was not following the task.<br>Skip this HIT to save your time if it is the 2nd situation.",
                type:   "error",
                confirmButtonColor: '#2B9DAB'
            }).catch(swal.noop);
 
            return false;
        }""" %  tuple([domain]*9)
    print """
        // search DB
        for(var i=0;i<%s_slots.length;i++){
            // find answer carrier
            var infoID = "%s_informable"+i.toString()
            var infoQuery = document.getElementById(infoID);
            // find search bar
            var footID = "%s_foot"+i.toString()
            var footQuery = document.getElementById(footID);
            if(infoQuery!=null && footQuery!=null){
                if(infoQuery.value!="dont care" && infoQuery.value!="not mentioned"){
                    footQuery.value = infoQuery.value
                } else{
                    footQuery.value = '';
                }
                var event = new Event('change');
                footQuery.dispatchEvent(event);
            }
        }
        
        swal({
            title:  "Info!",
            html:   "Search results have been shown.<br>You can type in the response now!",
            type:   "info",
            confirmButtonColor: '#2B9DAB'
        }).catch(swal.noop);
 
        document.getElementById("%sTableBackground").style.display='block';
        unlockResponse();
    }
    </script> 
    """ % tuple([domain]*4)

def printTaxiScript():
    print """
    <script type="text/javascript" class="init">
    $(document).ready(function() {
        // prevent submit button 
        $("#taxi_questions").submit(function(e){
            e.preventDefault();
            taxiSubmit();
            return false;
        });
        for (var count = 0; count <4; count++){
            $( "#taxi_informable"+count.toString() ).autocomplete({
                minLength:0,
                source: taxi_sources[count],
                messages: {
                    noResults: '',
                    results: function() {}
                },
                select: function(event, ui) {
                    $(this).val(ui.item.value);
                    $(this).trigger('change');
                }
            });
            $( "#taxi_informable"+count.toString() ).autocomplete("widget")
                .attr('style', 'max-height: 200px; overflow-y: auto; overflow-x: hidden;')
            $( "#taxi_informable"+count.toString() ).focus(function() {
                $(this).autocomplete('search', $(this).val())
            });
        };
        taxiInitSearchVal();
        for (var i=0;i<4;i++){
            if ($( "#taxi_informable"+i.toString() )!==undefined){
                $( "#taxi_informable"+i.toString() ).on('change paste keyup',function() {
                    $("#taxi_search").prop('disabled',false);
                    $("#taxi_search").removeClass('disabled');
                });
            }
        }
    });
    var taxi_color = ["black","white","red","yellow","blue",'grey'];
    var taxi_type  = ["toyota","skoda","bmw",'honda','ford','audi','lexus','volvo','volkswagen','tesla'];
    function getRandomNumber(){
        var number = "07";
        for (var i=0;i<9;i++){
            number += ~~(Math.random() * 10).toString();
        }
        return number 
    }
    function taxiSubmit(){

        // check whether the domain aligns to goal
        if (size_dict(goal["taxi"])==0){
            swal({
                title:  "Error!",
                html:   "It seems like you are choosing the wrong domain to work on.",
                type:   "error",
                confirmButtonColor: '#2B9DAB'
            }).catch(swal.noop);
 
            return false;
        } 
        // check whether the slot value pairs aligns to goal
        var isMatch = true;
        for(var i=0;i<taxi_slots.length;i++){
            var infoQuery = document.getElementById("taxi_informable"+i.toString());
            if(infoQuery!=null){
                var s = taxi_slots[i];
                var v = infoQuery.value;
                var slotMatch = false;
                if (v=='not mentioned' || v=='dont care'){
                    // if value is not mentioned or dontcare, approve it
                    slotMatch = true;
                } else if (s in goal["taxi"]["info"]){
                    if (v==goal["taxi"]["info"][s]) slotMatch = true
                } else {
                    // slot not specified in goal, should not allocate it value
                    // but allow destination and departure not pre-specified in goal
                    if (s=='destination' || s=='departure') slotMatch = true;
                }
                // for every slot it needs match
                isMatch = isMatch && slotMatch;
            }
        } 
        //if (!isMatch){
        //    swal({
        //        title:  "Error!",
        //        html:   "This occurs either:<br>1. You are not interpreting the semantics correctly, or<br>2. The user was not following the task.<br>Skip this HIT to save your time if it is the 2nd situation.",
        //        type:   "error",
        //        confirmButtonColor: '#2B9DAB'
        //    }).catch(swal.noop);
        //    return false;
        //}

        // proceed
        unlockResponse();

        // check booking successful
        if ($("#taxi_informable2").val()=='not mentioned' && $("#taxi_informable3").val()=='not mentioned'){
            $("#taxi_informable2").attr('class','errorq');
            $("#taxi_informable3").attr('class','errorq');
            $("#taxi_informable0").attr('class','bookq');
            $("#taxi_informable1").attr('class','bookq');
            document.getElementById("taxi_booked_table").hidden = true; 
            
            swal({
                title:  "Info!",
                html:   "Please ask the user and fill in <span class='emphasis'>at least</span> one of the highlighted areas to make a successful booking.",
                type:   "info",
                confirmButtonColor: '#2B9DAB'
            }).catch(swal.noop);

        } else if( $("#taxi_informable0").val()=='not mentioned' || $("#taxi_informable1").val()=='not mentioned'){
            $("#taxi_informable0").attr('class','bookq');
            $("#taxi_informable1").attr('class','bookq');
            if ($("#taxi_informable0").val()=='not mentioned') $("#taxi_informable0").attr('class','errorq');
            if ($("#taxi_informable1").val()=='not mentioned') $("#taxi_informable1").attr('class','errorq');
            $("#taxi_informable2").attr('class','bookq');
            $("#taxi_informable3").attr('class','bookq');
            document.getElementById("taxi_booked_table").hidden = true; 
            
            swal({
                title:  "Info!",
                html:   "Please ask the user and fill in the highlighted areas to make a successful booking.",
                type:   "info",
                confirmButtonColor: '#2B9DAB'
            }).catch(swal.noop);

        } else {
            // booking successful : show taxi information
            for (var i=0;i<4;i++){
                $("#taxi_informable"+i.toString()).attr('class','bookq');
            }
            document.getElementById("taxi_booked_table").hidden = false;
            var t_type = taxi_color[Math.floor(Math.random()*taxi_color.length)] + " "+ taxi_type[Math.floor(Math.random()*taxi_type.length)];
            var t_phone= getRandomNumber();
            document.getElementById("taxi_type").innerHTML = t_type;
            document.getElementById("taxi_phone").innerHTML= t_phone;
            $("#taxi_search").prop('disabled',true);
            $("#taxi_search").addClass('disabled');
            
            // update internal booking information
            taxi_book['booked'] = [{"type":t_type,"phone":t_phone}]
        
            swal({
                title:  "Info!",
                html:   "You can type in the response now!",
                type:   "info",
                confirmButtonColor: '#2B9DAB'
            }).catch(swal.noop);


        }
    }
    function taxiInitSearchVal(){
        for(var i=0;i<taxi_slots.length;i++){
            var infoID = "taxi_informable"+i.toString()
            var element = document.getElementById(infoID);
            if(element!=null){
                if(taxi_slots[i] in taxi_semi && taxi_slots[i]==element.name){
                    element.value = taxi_semi[taxi_slots[i]]; 
                }
            }
        }
    }
    function taxiBookInit(){
        
        // check for whether any booking has confirmed and initialise it 
        if (taxi_book['booked'].length==0){ // nothing is confirmed
            // do nothing
        } else{ // has a booking confirmed
            document.getElementById("taxi_booked_table").hidden = false;
            document.getElementById("taxi_type").innerHTML = taxi_book['booked'][0]['type'];
            document.getElementById("taxi_phone").innerHTML= taxi_book['booked'][0]['phone'];
            $("#taxi_search").prop('disabled',true);
            $("#taxi_search").addClass('disabled');
            unlockResponse();
            swal({
                title:  "Info!",
                html:   "The taxi has been booked.<br>Modify the query to change or carry on the conversation.",
                type:   "info",
                confirmButtonColor: '#2B9DAB'
            }).catch(swal.noop);


        }
    };
    </script>
    """



def printBookingDetails(domain, metadata):
    if domain=='restaurant':
        print """
        function %sFormat ( d ) {
            // `d` is the original data object for the row
            return '<form id="book_%s_questions" style="margin:10px 10px 10px 10px;">'+
            '<p>This section is <span class="emphasis">optional</span>. Fill it in only when the user is asking for <span class="emphasis">%s booking.</span></p>'+
            '<p>Break down the questions and ask the user <span class="emphasis">iteratively</span>. Don\\\'t cram everything in a single response.</p>'+
            '<table class="booktable" style="float: left">'+
            '<tr><td>Restaurant</td><td id="selected_restaurant">'+d.name+'</td></tr>'+
            '<tr>'+
                '<td>What <b>day</b> is it ?</td>'+
                '<td><input class="bookq" id="%s_book0" type="text" name="day" placeholder="choose" required oninvalid="this.setCustomValidity(\\\'Please ask the user about this field and fill it in before booking\\\')" onchange="this.setCustomValidity(\\\'\\\')"/></td>'+
            '</tr>'+
            '<tr>'+
                '<td>What <b>time</b> is it ?</td>'+
                '<td><input class="bookq" id="%s_book1" type="text" name="time" placeholder="choose" required oninvalid="this.setCustomValidity(\\\'Please ask the user about this field and fill it in before booking\\\')" onchange="this.setCustomValidity(\\\'\\\')"/></td>'+
            '</tr>'+
            '<tr>'+
                '<td><b>How many</b> people ?</td>'+
                '<td><input class="bookq" id="%s_book2" type="text" name="people" placeholder="choose" required oninvalid="this.setCustomValidity(\\\'Please ask the user about this field and fill it in before booking\\\')" onchange="this.setCustomValidity(\\\'\\\')"/></td>'+
            '</tr>'+
            '</table>'+
            '<div style="float:left">'+
            '<input id="%s_book_btn" type="submit" class="button hint" value="Book" style="margin:0px 0px 0px 10px;">'+
            '<table class="booktable" style="margin:10px 0px 10px 10px;">'+
            '<tr><td id="%s_book_status" hidden></td></tr>'+
            '<tr><td id="%s_book_reference" hidden></td></tr>'+
            '</table></div></form>'
        }""" % tuple([domain]*9)
        print """
        function %sBookInit() {
            for (var i=0;i<3;i++){
                if ($( "#%s_book"+i.toString() )!==undefined){
                    $( "#%s_book"+i.toString() ).on('change paste keyup',function() {
                        %sBookCheck();
                    });
                    %sBookCheck();
                }
            }
            // check for whether any booking has confirmed and initialise it 
            if (%s_book['booked'].length==0){ // nothing is confirmed
                // do nothing
            } else{ // has at least one booking confirmed
                // get the values from the current row child
                var venue = document.getElementById("selected_%s").innerText;

                for (var i=0;i<%s_book['booked'].length;i++){
                    // validate the current values with any given booking histories
                    if (%s_book['booked'][i]['name']==venue){ // if matches
                        document.getElementById("%s_book_status").hidden = false;
                        document.getElementById("%s_book_status").innerHTML = "Booking was <span class='emphasis'>successful</span>, table will be reserved for <span class='emphasis'>15 mins</span>."
                        document.getElementById("%s_book_reference").hidden = false;
                        document.getElementById("%s_book_reference").innerHTML = "Reference number is : <span class='emphasis'>"+%s_book['booked'][i]['reference']+"</span>."
                        document.getElementById("%s_book_btn").disabled = true;
                        $("#%s_book_btn").addClass("disabled");
                        break;
                    }
                }
            }

        };
        function %sBookCheck(){
            for (var j=0;j<3;j++){
                if ($( "#%s_book"+j.toString() )!==undefined){
                    var wgt = document.getElementById("%s_book"+j.toString());
                    window["%s_book"][wgt.name] = wgt.value;
                }
            }
            for (var j=0;j<3;j++){
                if ($( "#%s_book"+j.toString() )!==undefined && $("#%s_book"+j.toString()).val()==""){
                    $("#%s_book_btn").val("Hint");
                    $("#%s_book_btn").attr('class','button hint');
                    $("#%s_book_btn").prop('disabled',false);
                    return true;
                }
            }
            $("#%s_book_btn").val("Book");
            $("#%s_book_btn").attr('class','button lookup');
            $("#%s_book_btn").prop('disabled',false);
        }""" %tuple([domain]*28)

        print """
        function %sBookSuggestion(){
            var %sBookIndexes = [2,4,0];
            for (var idx=0;idx<%sBookIndexes.length;idx++){
                $( "#%s_book"+idx.toString() ).autocomplete({
                    minLength:0,
                    source: default_sources[%sBookIndexes[idx]],
                    messages: {
                        noResults: '',
                        results: function() {}
                    },
                    select: function(event, ui) {
                        $(this).val(ui.item.value);
                        $(this).trigger('change');
                    }
                });
                $( "#%s_book"+idx.toString() ).autocomplete("widget").attr('style', 'max-height: 200px; overflow-y: auto; overflow-x: hidden;')
                $( "#%s_book"+idx.toString() ).focus(function() {
                    $(this).autocomplete('search', $(this).val())
                });
                // initialise value from history
                var slot = $( "#%s_book"+idx.toString() ).attr("name");
                if (slot in %s_book){
                    $( "#%s_book"+idx.toString() ).val(%s_book[slot]);
                    if (%s_book[slot]==""){
                        $("#%s_book_btn").val("Hint");
                    }
                }
            }
        };
        function %sBookConfirmation(){
            // decide whether the item is bookable for not
            var %sBookIndexes = [2,0,0];
            var canBook = true;
            for (var idx=0;idx<%sBookIndexes.length;idx++){
                var minput = document.getElementById( "%s_book"+idx.toString() )
                if (minput.value==""){
                    minput.className = 'errorq';
                    canBook = false;
                } else{
                    minput.className = 'bookq';
                }
            } if (!canBook){
            
                swal({
                    title:  "Info!",
                    html:   "In order to book, ask the user for more details (highlighted) to complete the booking form.",
                    type:   "info",
                    confirmButtonColor: '#2B9DAB'
                }).catch(swal.noop);

                return canBook;
            }
            // checking each value is valid
            var isMatch = true;
            var isCorrect = true;
            for (var idx=0;idx<%sBookIndexes.length;idx++){
                var minput = document.getElementById( "%s_book"+idx.toString() );
                if (minput!=null){
                    var s = minput.name;
                    var v = minput.value;
                    var slotMatch = false;
                    var slotCorrect = false;
                    if (!(["book"] in goal["%s"])){
                        // request scenario, default correct
                        slotMatch = true;
                        slotCorrect = true;
                    } else if (s in goal["%s"]["book"] || s in goal["%s"]["fail_book"]){
                        if (s in goal["%s"]["book"] && v==goal["%s"]["book"][s]) {
                            slotMatch = true;
                            slotCorrect = true;
                        }
                        if (s in goal["%s"]["fail_book"] && v==goal["%s"]["fail_book"][s]) slotMatch = true
                    } else {
                        // slot not specified in goal, should not allocate it value
                        slotMatch = false;
                    }
                    // for every slot it needs match
                    isMatch = isMatch && slotMatch;
                    isCorrect = isCorrect && slotCorrect;
                }
            } 
            //if (!isMatch){
            //    swal({
            //        title:  "Error!",
            //        html:   "This occurs either:<br>1. You are not interpreting the semantics correctly, or<br>2. The user was not following the task.<br>Skip this HIT to save your time if it is the 2nd situation.",
            //        type:   "error",
            //        confirmButtonColor: '#2B9DAB'
            //    }).catch(swal.noop);
            //    return false;
            //}
            
            // if the criteria exactly match, a successful booking
            if (isCorrect){
                if (goal['%s']['book']['invalid']==true){
                    goal['%s']['book']['pre_invalid']=true;
                    goal['%s']['book']['invalid']=false;
                }
                var venue = document.getElementById("selected_restaurant").innerText;
                document.getElementById("%s_book_status").hidden = false;
                document.getElementById("%s_book_status").innerHTML = "Booking was <span class='emphasis'>successful</span>. The table will be reserved for 15 minutes."
                document.getElementById("%s_book_reference").hidden = false;
                var ref = genRef();
                document.getElementById("%s_book_reference").innerHTML = "Reference number is : <span class='emphasis'>"+ref+"</span>."
                document.getElementById("%s_book_btn").disabled = true;
                $("#%s_book_btn").addClass("disabled");
                
                // update internal booking information
                var idExist = false;
                for (var i=0;i<%s_book['booked'].length;i++){
                    if (%s_book['booked'][i]['name']==venue){
                        %s_book['booked'][i] = {"name":venue,"reference":ref}
                        idExist = true;
                    }
                } if (!idExist){
                    %s_book['booked'].push({"name":venue,"reference":ref})
                }
            } else{
                // booking is invalid
                goal['%s']['book']['pre_invalid']=true;
                goal['%s']['book']['invalid']=false;
                document.getElementById("%s_book_status").hidden = false;
                document.getElementById("%s_book_status").innerHTML = "Booking was <span class='emphasis'>unsuccessful</span>."
                document.getElementById("%s_book_reference").hidden = false;
                document.getElementById("%s_book_reference").innerHTML = "Please ask the user to book another day or time slot."
                document.getElementById("%s_book_btn").disabled = true;
                $("#%s_book_btn").addClass("disabled");
            } 
            swal({
                title:  "Info!",
                html:   "You are ready to reply!",
                type:   "info",
                confirmButtonColor: '#2B9DAB'
            }).catch(swal.noop);

        };""" % tuple([domain]*47)
    if domain=='hotel':
        print """
        function %sFormat ( d ) {
        // `d` is the original data object for the row
            return '<form id="book_%s_questions" style="margin:10px 10px 10px 10px;">'+
            '<p>This section is <span class="emphasis">optional</span>. Fill it in only when the user is asking for <span class="emphasis">%s booking.</span></p>'+
            '<p>Break down the questions and ask the user <span class="emphasis">iteratively</span>. Don\\\'t cram everything in a single response.</p>'+
            '<table class="booktable" style="float: left">'+
            '<tr><td>Hotel</td><td id="selected_hotel">'+d.name+'</td></tr>'+
            '<tr>'+
                '<td>What <b>day</b> is it ?</td>'+
                '<td><input class="bookq" id="%s_book0" type="text" name="day" placeholder="choose" required oninvalid="this.setCustomValidity(\\\'Please ask the user about this field and fill it in before booking\\\')" onchange="this.setCustomValidity(\\\'\\\')"/></td>'+
            '</tr>'+
            '<tr>'+
                '<td>What <b>many days</b> does the user want to stay ?</td>'+
                '<td><input class="bookq" id="%s_book1" type="text" name="stay" placeholder="choose" required oninvalid="this.setCustomValidity(\\\'Please ask the user about this field and fill it in before booking\\\')" onchange="this.setCustomValidity(\\\'\\\')"/></td>'+
            '</tr>'+
            '<tr>'+
                '<td><b>How many</b> people ?</td>'+
                '<td><input class="bookq" id="%s_book2" type="text" name="people" placeholder="choose" required oninvalid="this.setCustomValidity(\\\'Please ask the user about this field and fill it in before booking\\\')" onchange="this.setCustomValidity(\\\'\\\')"/></td>'+
            '</tr>'+
            '</table>'+
            '<div style="float:left">'+
            '<input id="%s_book_btn" type="submit" class="button hint" value="Hint" style="margin:0px 0px 0px 10px;">'+
            '<table class="booktable" style="margin:10px 0px 10px 10px;">'+
            '<tr><td id="%s_book_status" hidden></td></tr>'+
            '<tr><td id="%s_book_reference" hidden></td></tr>'+
            '</table></div></form>'
        }""" % tuple([domain]*9)
        print """
        function %sBookInit() {
            for (var i=0;i<3;i++){
                if ($( "#%s_book"+i.toString() )!==undefined){
                    $( "#%s_book"+i.toString() ).on('change paste keyup',function() {
                        %sBookCheck();
                    });
                    %sBookCheck();
                }
            }
            // check for whether any booking has confirmed and initialise it 
            if (%s_book['booked'].length==0){ // nothing is confirmed
                // do nothing
            } else{ // has at least one booking confirmed
                // get the values from the current row child
                var venue = document.getElementById("selected_%s").innerText;

                for (var i=0;i<%s_book['booked'].length;i++){
                    // validate the current values with any given booking histories
                    if (%s_book['booked'][i]['name']==venue){ // if matches
                        document.getElementById("%s_book_status").hidden = false;
                        document.getElementById("%s_book_status").innerHTML = "Booking was <span class='emphasis'>successful</span>."
                        document.getElementById("%s_book_reference").hidden = false;
                        document.getElementById("%s_book_reference").innerHTML = "Reference number is : <span class='emphasis'>"+%s_book['booked'][i]['reference']+"</span>."
                        document.getElementById("%s_book_btn").disabled = true;
                        $("#%s_book_btn").addClass("disabled");
                        break;
                    }
                }
            }

        };
        function %sBookCheck(){
            for (var j=0;j<3;j++){
                if ($( "#%s_book"+j.toString() )!==undefined){
                    var wgt = document.getElementById("%s_book"+j.toString());
                    window["%s_book"][wgt.name] = wgt.value;
                }
            }
            for (var j=0;j<3;j++){
                if ($( "#%s_book"+j.toString() )!==undefined && $("#%s_book"+j.toString()).val()==""){
                    $("#%s_book_btn").val("Hint");
                    $("#%s_book_btn").attr('class','button hint');
                    $("#%s_book_btn").prop('disabled',false);
                    return true;
                }
            }
            $("#%s_book_btn").val("Book");
            $("#%s_book_btn").attr('class','button lookup');
            $("#%s_book_btn").prop('disabled',false);
        }""" %tuple([domain]*28)

        print """
        function %sBookSuggestion(){
            var %sBookIndexes = [2,0,0];
            for (var idx=0;idx<%sBookIndexes.length;idx++){
                $( "#%s_book"+idx.toString() ).autocomplete({
                    minLength:0,
                    source: default_sources[%sBookIndexes[idx]],
                    messages: {
                        noResults: '',
                        results: function() {}
                    },
                    select: function(event, ui) {
                        $(this).val(ui.item.value);
                        $(this).trigger('change');
                    }
                });
                $( "#%s_book"+idx.toString() ).autocomplete("widget").attr('style', 'max-height: 200px; overflow-y: auto; overflow-x: hidden;')
                $( "#%s_book"+idx.toString() ).focus(function() {
                    $(this).autocomplete('search', $(this).val())
                });
                // initialise value from history
                var slot = $( "#%s_book"+idx.toString() ).attr("name");
                if (slot in %s_book){
                    $( "#%s_book"+idx.toString() ).val(%s_book[slot]);
                }
            }
        };
        function %sBookConfirmation(){
            var %sBookIndexes = [2,0,0];
            var canBook = true;
            for (var idx=0;idx<%sBookIndexes.length;idx++){
                var minput = document.getElementById( "%s_book"+idx.toString() )
                if (minput.value=="not mentioned" || minput.value==""){
                    minput.className = 'errorq';
                    canBook = false;
                } else{
                    minput.className = 'bookq';
                }
            }
            if (!canBook){
                swal({
                    title:  "Info!",
                    html:   "In order to book, ask the user for more details (highlighted) to complete the booking form.",
                    type:   "info",
                    confirmButtonColor: '#2B9DAB'
                }).catch(swal.noop);

                return canBook;
            }
            
            // checking each value is valid
            var isMatch = true;
            var isCorrect = true;
            for (var idx=0;idx<%sBookIndexes.length;idx++){
                var minput = document.getElementById( "%s_book"+idx.toString() );
                if (minput!=null){
                    var s = minput.name;
                    var v = minput.value;
                    var slotMatch = false;
                    var slotCorrect = false;
                    if (!(["book"] in goal["%s"])){
                        // request scenario, default correct
                        slotMatch = true;
                        slotCorrect = true;
                    }
                    else if (s in goal["%s"]["book"] || s in goal["%s"]["fail_book"]){
                        if (s in goal["%s"]["book"] && v==goal["%s"]["book"][s]){
                            slotMatch = true;
                            slotCorrect = true;
                        }
                        if (s in goal["%s"]["fail_book"] && v==goal["%s"]["fail_book"][s]) slotMatch = true
                    } else {
                        // slot not specified in goal, should not allocate it value
                        slotMatch = false;
                    }
                    // for every slot it needs match
                    isMatch = isMatch && slotMatch;
                    isCorrect = isCorrect && slotCorrect;
                }
            } 
            //if (!isMatch){
            //    swal({
            //        title:  "Error!",
            //        html:   "This occurs either:<br>1. You are not interpreting the semantics correctly, or<br>2. The user was not following the task.<br>Skip this HIT to save your time if it is the 2nd situation.",
            //        type:   "error",
            //        confirmButtonColor: '#2B9DAB'
            //    }).catch(swal.noop); 
            //    return false;
            //}
            // if the criteria exactly match, a successful booking
            if (isCorrect){
                if (goal['%s']['book']['invalid']==true){
                    goal['%s']['book']['pre_invalid']=true;
                    goal['%s']['book']['invalid']=false;
                }
                var venue = document.getElementById("selected_hotel").innerText;
                document.getElementById("%s_book_status").hidden = false;
                document.getElementById("%s_book_status").innerHTML = "Booking was <span class='emphasis'>successful</span>."
                document.getElementById("%s_book_reference").hidden = false;
                var ref = genRef();
                document.getElementById("%s_book_reference").innerHTML = "Reference number is : <span class='emphasis'>"+ref+"</span>."
                document.getElementById("%s_book_btn").disabled = true;
                $("#%s_book_btn").addClass("disabled");
                
                // update internal booking information
                var idExist = false;
                for (var i=0;i<%s_book['booked'].length;i++){
                    if (%s_book['booked'][i]['name']==venue){
                        %s_book['booked'][i] = {"name":venue,"reference":ref}
                        idExist = true;
                    }
                } if (!idExist){
                    %s_book['booked'].push({"name":venue,"reference":ref})
                }
            } else{
                // booking is invalid
                goal['%s']['book']['pre_invalid']=true;
                goal['%s']['book']['invalid']=false;
                document.getElementById("%s_book_status").hidden = false;
                document.getElementById("%s_book_status").innerHTML = "Booking was <span class='emphasis'>unsuccessful</span>."
                document.getElementById("%s_book_reference").hidden = false;
                document.getElementById("%s_book_reference").innerHTML = "Please ask the user to book another day or a shorter stay."
                document.getElementById("%s_book_btn").disabled = true;
                $("#%s_book_btn").addClass("disabled");
            } 
            
            swal({
                title:  "Info!",
                html:   "You are ready to reply!",
                type:   "info",
                confirmButtonColor: '#2B9DAB'
            }).catch(swal.noop);



        };""" % tuple([domain]*45)
   
    if domain=='train':
        print """
        function %sFormat ( d ) {
            // `d` is the original data object for the row
            return '<form id="book_%s_questions" style="margin:10px 10px 10px 10px;">'+
            '<p>This section is <span class="emphasis">optional</span>. Fill it in only when the user is asking for <span class="emphasis">%s booking.</span></p>'+
            '<table class="booktable" style="float:left">'+
            '<tr><td>Train ID</td><td id="selected_train">'+d.trainID+'</td></tr>'+
            '<tr><td>Price</td><td id="selected_price">'+d.price+'</td></tr>'+
            '<tr>'+
                '<td><b>How many</b> tickets ?</td>'+
                '<td><input class="bookq" id="%s_book0" type="text" name="people" placeholder="choose" required oninvalid="this.setCustomValidity(\\\'Please ask the user about this field and fill it in before booking\\\')" onchange="this.setCustomValidity(\\\'\\\')"/></td>'+
            '</tr>'+
            '</table>'+
            '<div style="float:left">'+
            '<input id="%s_book_btn" type="submit" class="button hint" value="Hint" style="margin:0px 0px 0px 10px;">'+
            '<table class="booktable" style="margin:10px 0px 10px 10px;">'+
            '<tr><td id="%s_book_status" hidden></td></tr>'+
            '<tr><td id="%s_book_reference" hidden></td></tr>'+
            '</table></div></form>'
        }""" % tuple([domain]*7)
        print """
        function %sBookInit() {
            // add book buton change listener and check for initial phase
            for (var i=0;i<3;i++){
                if ($( "#%s_book"+i.toString() )!==undefined){
                    $( "#%s_book"+i.toString() ).on('change paste keyup',function() {
                        %sBookCheck();
                    });
                    %sBookCheck();
                }
            }
            // check for whether any booking has confirmed and initialise it 
            if (%s_book['booked'].length==0){ // nothing is confirmed
                // do nothing
            } else{ // has at least one booking confirmed
                // get the values from the current row child
                var venue = document.getElementById("selected_%s").innerText;
                var price = document.getElementById("selected_price").innerText;
                price = parseFloat(price);

                for (var i=0;i<%s_book['booked'].length;i++){
                    // validate the current values with any given booking histories
                    if (%s_book['booked'][i]['trainID']==venue){ // if matches
                        document.getElementById("%s_book_status").hidden = false;
                        document.getElementById("%s_book_status").innerHTML = "Booking was <span class='emphasis'>successful</span>, the total fee is <span class='emphasis'>"+Math.floor(price*parseInt(document.getElementById( "%s_book0" ).value)*100)/100+" GBP</span> payable at the station ."
                        document.getElementById("%s_book_reference").hidden = false;
                        document.getElementById("%s_book_reference").innerHTML = "Reference number is : <span class='emphasis'>"+%s_book['booked'][i]['reference']+"</span>."
                        document.getElementById("%s_book_btn").disabled = true;
                        $("#%s_book_btn").addClass("disabled");
                        break;
                    }
                }
            }
        };
        function %sBookCheck(){
            for (var j=0;j<1;j++){
                if ($( "#%s_book"+j.toString() )!==undefined){
                    var wgt = document.getElementById("%s_book"+j.toString());
                    window["%s_book"][wgt.name] = wgt.value;
                }
            }
            for (var j=0;j<3;j++){
                if ($( "#%s_book"+j.toString() )!==undefined && $("#%s_book"+j.toString()).val()==""){
                    $("#%s_book_btn").val("Hint");
                    $("#%s_book_btn").attr('class','button hint');
                    $("#%s_book_btn").prop('disabled',false);
                    return true;
                }
            }
            $("#%s_book_btn").val("Book");
            $("#%s_book_btn").attr('class','button lookup');
            $("#%s_book_btn").prop('disabled',false);
        }""" %tuple([domain]*29)
        print """
        function %sBookSuggestion(){
            var %sBookIndexes = [0];
            for (var idx=0;idx<%sBookIndexes.length;idx++){
                $( "#%s_book"+idx.toString() ).autocomplete({
                    minLength:0,
                    source: default_sources[%sBookIndexes[idx]],
                    messages: {
                        noResults: '',
                        results: function() {}
                    },
                    select: function(event, ui) {
                        $(this).val(ui.item.value);
                        $(this).trigger('change');
                    }
                });
                $( "#%s_book"+idx.toString() ).autocomplete("widget").attr('style', 'max-height: 200px; overflow-y: auto; overflow-x: hidden;')
                $( "#%s_book"+idx.toString() ).focus(function() {
                    $(this).autocomplete('search', $(this).val())
                });
                // initialise value from history
                var slot = $( "#%s_book"+idx.toString() ).attr("name");
                if (slot in %s_book){
                    $( "#%s_book"+idx.toString() ).val(%s_book[slot]);
                }
            }
        };
        function %sBookConfirmation(){
            var %sBookIndexes = [0];
            var canBook = true;
            for (var idx=0;idx<%sBookIndexes.length;idx++){
                var minput = document.getElementById( "%s_book"+idx.toString() )
                if (minput.value=="not mentioned" || minput.value==""){
                    minput.className = 'errorq';
                    canBook = false;
                } else{
                    minput.className = 'bookq';
                }
            } if (!canBook){
                swal({
                    title:  "Info!",
                    html:   "In order to book, ask the user for more details (highlighted) to complete the booking form.",
                    type:   "info",
                    confirmButtonColor: '#2B9DAB'
                }).catch(swal.noop);

                return canBook;
            }

            // checking each value is valid
            var isMatch = true;
            for (var idx=0;idx<%sBookIndexes.length;idx++){
                var minput = document.getElementById( "%s_book"+idx.toString() );
                if (minput!=null){
                    var s = minput.name;
                    var v = minput.value;
                    var slotMatch = false;
                    if (!(["book"] in goal["%s"])){
                        // request scenario, default correct
                        slotMatch = true;
                    } else if (s in goal["%s"]["book"] || s in goal["%s"]["fail_book"]){
                        if (s in goal["%s"]["book"] && v==goal["%s"]["book"][s]) slotMatch = true
                        if (s in goal["%s"]["fail_book"] && v==goal["%s"]["fail_book"][s]) slotMatch = true
                    } else {
                        // slot not specified in goal, should not allocate it value
                        slotMatch = false;
                    }
                    // for every slot it needs match
                    isMatch = isMatch && slotMatch;
                }
            }
            // if (!isMatch){
            //    swal({
            //        title:  "Error!",
            //        html:   "This occurs either:<br>1. You are not interpreting the semantics correctly, or<br>2. The user was not following the task.<br>Skip this HIT to save your time if it is the 2nd situation.",
            //        type:   "error",
            //        confirmButtonColor: '#2B9DAB'
            //    }).catch(swal.noop);
            // 
            //    return false;
            //}

            // get the values from the currently opened row child
            var venue = document.getElementById("selected_%s").innerText;
            var price = document.getElementById("selected_price").innerText;
            price = parseFloat(price);

            // change UI status
            document.getElementById("%s_book_status").hidden = false;
            document.getElementById("%s_book_status").innerHTML = "Booking was <span class='emphasis'>successful</span>, the total fee is <span class='emphasis'>"+Math.floor(price*parseInt(document.getElementById( "%s_book0" ).value)*100)/100+" GBP</span> payable at the station ."
            document.getElementById("%s_book_reference").hidden = false;
            var ref = genRef();
            document.getElementById("%s_book_reference").innerHTML = "Reference number is : <span class='emphasis'>"+ref+"</span>."
            document.getElementById("%s_book_btn").disabled = true;
            $("#%s_book_btn").addClass("disabled");

            // update internal booking information
            var idExist = false;
            for (var i=0;i<%s_book['booked'].length;i++){
                if (%s_book['booked'][i]['trainID']==venue){
                    %s_book['booked'][i] = {"trainID":venue,"reference":ref}
                    idExist = true;
                }
            } if (!idExist){
                %s_book['booked'].push({"trainID":venue,"reference":ref})
            }
            swal({
                title:  "Info!",
                html:   "You are ready to reply!",
                type:   "info",
                confirmButtonColor: '#2B9DAB'
            }).catch(swal.noop);


        };""" % tuple([domain]*36)
    
    if domain=='hospital':
        print """
        function %sFormat ( d ) {
            // `d` is the original data object for the row
            return '<form id="book_%s_questions">'+
            '<p>This section is <span class="emphasis">optional</span>. Do it only when the user is asking for <span class="emphasis">%s booking.</span></p>'+
            '<table class="booktable">'+
            '<tr><td>Department</td><td id="selected_department">'+d.department+'</td></tr>'+
            '<tr><td>Contact</td><td id="selected_contact">'+d.phone+'</td></tr>'+
            '</table>'+
            '<div>'+
            '<input id="%s_book_btn" type="submit" class="button lookup" value="Check availability" style="margin:10px 0px 0px 0px;">'+
            '<table class="booktable" style="margin:10px 0px 0px 0px;">'+
            '<tr><td id="%s_book_status" hidden></td></tr>'+
            '<tr><td id="%s_book_reference" hidden></td></tr>'+
            '</table></div></form>'
        }""" % tuple([domain]*6)
        print """
        function %sBookSuggestion(){};
        function %sBookInit(){
        
            // check for whether any booking has confirmed and initialise it 
            if (%s_book['booked'].length==0){ // nothing is confirmed
                // do nothing
            } else{ // has at least one booking confirmed
                // get the values from the current row child
                var venue = document.getElementById("selected_department").innerText;

                for (var i=0;i<%s_book['booked'].length;i++){
                    // validate the current values with any given booking histories
                    if (%s_book['booked'][i]['department']==venue){ // if matches
                        document.getElementById("%s_book_status").hidden = false;
                        document.getElementById("%s_book_status").innerHTML = "Booking was <span class='emphasis'>successful</span>, the arranged time slot is <span class='emphasis'>"+%s_book['booked'][i]['time']+"</span>.";
                        document.getElementById("%s_book_reference").hidden = false;
                        document.getElementById("%s_book_reference").innerHTML = "Reference number is : <span class='emphasis'>"+%s_book['booked'][i]['reference']+"</span>."
                        document.getElementById("%s_book_btn").disabled = true;
                        $("#%s_book_btn").addClass("disabled");
                        break;
                    }
                }
            }
        };
        function %sBookConfirmation(){
            var venue = document.getElementById("selected_department").innerText;
            var phone = document.getElementById("selected_contact").innerText;
            time = genTime();
            document.getElementById("%s_book_status").hidden = false;
            document.getElementById("%s_book_status").innerHTML = "Booking was <span class='emphasis'>successful</span>, the arranged time slot is <span class='emphasis'>"+time[0]+", next "+time[1]+"</span>.";
            document.getElementById("%s_book_reference").hidden = false;
            var ref = genRef();
            document.getElementById("%s_book_reference").innerHTML = "Reference number is : <span class='emphasis'>"+ref+"</span>."
            document.getElementById("%s_book_btn").disabled = true;
            $("#%s_book_btn").addClass("disabled");

            // update internal booking information
            var idExist = false;
            for (var i=0;i<%s_book['booked'].length;i++){
                if (%s_book['booked'][i]['department']==venue){
                    %s_book['booked'][i] = {"department":venue,"reference":ref,"time":time[0]+", next "+time[1]}
                    idExist = true;
                }
            } if (!idExist){
                %s_book['booked'].push({"department":venue,"reference":ref,"time":time[0]+", next "+time[1]})
            }

            swal({
                title:  "Info!",
                html:   "You are ready to reply!",
                type:   "info",
                confirmButtonColor: '#2B9DAB'
            }).catch(swal.noop);


        };""" % tuple([domain]*24)
 



