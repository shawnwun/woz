######################################################################
######################################################################
#  Copyright Tsung-Hsien Wen, Cambridge Dialogue Systems Group, 2017 #
######################################################################
######################################################################

#! /usr/bin/python
# -*- coding: utf-8 -*-

__author__="Shawn Wen"
__date__ ="$17-Mar-2017 17:32:34$"

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
from util.printfunctions import *

def include(fileName):
    f = open(fileName, "r")

    print "<!-- include('", fileName,"') -->"
    for line in f:
        print line,

def getTextFromNode(node):
    text = ""
    for n in node.childNodes:
      if n.nodeType == Node.TEXT_NODE:
        text += n.data

    text = text.strip()
    text = re.sub("\s+" , " ", text)
   
    return text


print "Content-type: text/html\n\n"

form = cgi.FieldStorage()
if form.getfirst('success',False)=='true':
    showComplete = True
else: 
    showComplete = False


print '<H2 class="emphasis" id="locationWarning"></H2><BR>'
print """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<HTML>
    <HEAD>
        <TITLE>Amazon Mechanical Turk - Restaurant Information System</TITLE>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>

        <link rel="stylesheet" href="util/mturk.css" TYPE="text/css" MEDIA="screen">
        <script src="https://code.jquery.com/jquery-1.9.1.js"></script>
        <script src="https://code.jquery.com/ui/1.10.3/jquery-ui.js"></script>
        <script type="text/javascript" src="util/tabber-minimized.js"></script>
        <script type="text/javascript" src="util/feedback.js"></script>
        <script type="text/javascript" src="util/submitTurn.js"></script>
        <script src="util/sweetalert2/sweetalert2.min.js"></script>
        <link rel="stylesheet" href="util/sweetalert2/sweetalert2.min.css">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/core-js/2.4.1/core.js"></script>
       
        <script type="text/javascript">
            /* Optional: Temporarily hide the "tabber" class so it does not "flash"*/
            document.write('<style type="text/css">.tabber{display:none;}<\/style>');
        </script>
        <script type="text/javascript" src="https://www.google.com/jsapi?key=ABQIAAAA-fK3SsIXeXJuKpgW1hT6kRRwPF2u2lm2QTXas2nGIPxzsfKaMRRV4qNXAn_UlCjcNRodB7mb2gBIVw"></script>
        <script>
            google.load("search", "1",{callback: getLocation});
            var glocation = "";
            function getLocation() {
                if (google.loader.ClientLocation) {
                    glocation += google.loader.ClientLocation.address.country_code;
                    glocation += ":";
                    glocation += google.loader.ClientLocation.address.region;
                    glocation += ":";
                    glocation += google.loader.ClientLocation.address.city;
                } if (glocation.lastIndexOf('US', 0) != 0) {
                    document.getElementById("locationWarning").innerHTML = "This HIT can be completed only by native speakers of English from USA. If it is found that this HIT was completed from other location than USA then it will be automatically rejected.";
                }
            }
        </script>
    </HEAD>
    <BODY>
    <!--
    <BODY onload="tabberAutomatic();disableFeedback();" >
    -->
        <script type="text/javascript">
        var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
        document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));
        </script>
        <script type="text/javascript">
        try {
        var pageTracker = _gat._getTracker("UA-349008-12");
        } catch(err) {}</script>
"""


status = None
assignmentId = form.getfirst('assignmentId','None')
workerId = form.getfirst('workerId','None')
hitId = form.getfirst('hitId','None')
goal = 'None'
task = 'None'
caller = "10004@eldoradovm1.eng.cam.ac.uk"
callee = "11111@eldoradovm1.eng.cam.ac.uk"
dialogue = []

if assignmentId == 'ASSIGNMENT_ID_NOT_AVAILABLE':
    status = "preview"
    print '<H2 class="emphasis">This is a preview of the HIT. Accept the HIT before you start the task.</H2><BR>'
    caller = "10005@eldoradovm1.eng.cam.ac.uk"
    print """
    <script type="text/javascript">
        pageTracker._trackPageview('/~mh521/G1/preview');
    </script>
"""
elif assignmentId == 'None':
    status = "test"
    print '<H2 class="emphasis">This page is not loaded from MTURK.</H2>'
    caller = "10007@eldoradovm1.eng.cam.ac.uk"
    print """
    <script type="text/javascript">
        pageTracker._trackPageview('/~mh521/G1/test');
    </script>
"""
else:
    status = "accepted"
    # assignmentId was provided
    caller = "10006@eldoradovm1.eng.cam.ac.uk"
    print """
    <script type="text/javascript">
        pageTracker._trackPageview('/~mh521/G1/accepted');
    </script>
"""

"""
if not workerId == 'None':
    vw = verifyWorker(workerId)
    if vw == ">20in24h":
        print <H2 class="emphasis">You have submitted more than 20 HITs in the
        last 24 hours. You are welcome to come after 24 hours and do another 20 HITs.
        Please, bookmark the following
        <a target="_top" href="https://www.mturk.com/mturk/searchbar?searchWords=automated+restaurant+information">
        link on MTURK search</a>. </H2>
        </BODY>
    <HTML>
        sys.exit()

    if vw == ">100in4w":
        print <H2 class="emphasis">You have submitted more than 100 HITs in the
        last four weeks. You are welcome to come after four weeks and do another 100 HITs.
        Please, bookmark the following
        <a target="_top" href="https://www.mturk.com/mturk/searchbar?searchWords=automated+toshiba+restaurant+information">
        link on MTURK search</a>. </H2>
        </BODY>
    <HTML>
        sys.exit()
"""
###################################################################
####################### load task from file #######################
###################################################################
lock = LockFile('lock/tasks.lock')
with lock:
    # load the current task number
    listFile = 'lock/taskList' #if not showComplete else 'tmp/finishedList'
    fin = file(listFile)
    currentIdx = int(fin.readline().replace('\n',''))
    tasks = [x.replace('\n','') for x in fin.readlines()]
    fin.close() 
    # if there are no tasks left, display busy message
    if len(tasks)==0:
        print """
        <div id="notfound" class="notfound">
        <center><span class="emphasis">[Busy]</span> All the tasks are being worked on. Please come back later!</center>
        </div>
        <div id="footer" style="width:95%">
        <center>Posted by: Dialogue Systems Group</center>
        <center>Contact: dialoguesystems@gmail.com</center>
        </div>
        """
        exit() 
    # increment current index and save it back
    taskfile = tasks[currentIdx%len(tasks)]
    #tasks.remove(taskfile)
    fout = file(listFile,'w')
    fout.write('\n'.join([str(x) for x in [currentIdx+1]+tasks]))
    fout.close()

fin = file('tempTasks/'+taskfile)
data = json.load(fin)
fin.close()
###################################################################
# task metadata
taskLen = data['goal']['messageLen']
taskID  = taskfile.replace('.json','')

msgs = data['goal']['message']
while taskLen<len(msgs) and \
        (   'reference number' in msgs[taskLen] or 
            'contact number' in msgs[taskLen] or
            'commute between' in msgs[taskLen-1]  ):
    taskLen = taskLen+1
taskLen = min(taskLen,len(msgs))

for i in range(len(data['goal']['message'])):
    data['goal']['message'][i] = data['goal']['message'][i].replace('\n','')


#taskLen = len(msgs)
taskMsg = '<ul><li>'+'.</li><li>'.join(data['goal']['message'][:taskLen])+'</li></ul>'

if taskLen==len(msgs):
    taskMsg += "<div id='taskEnd'><center>--- The End ---</center></div>"


print """
<script>
    var taskID = "%(taskID)s";
    var task = "%(task)s";
    var assignmentId = "%(assignmentId)s";
    var workerId = "%(workerId)s";
    var hitId = "%(hitId)s";
    var goal = %(goal)s;
    var msgLen = %(msgLen)d;
</script>""" % {'taskID':taskID,'task':taskMsg,'caller':caller,'callee':callee,
        'assignmentId':assignmentId,'workerId':workerId,'hitId':hitId,
        'goal':json.dumps(data['goal']),'msgLen':taskLen}

# decide system or user turn config
dialog = data['log']
# remove duplicated turns
idx = 0
while idx<len(dialog)-1:
    if len(dialog[idx]['metadata'])==len(dialog[idx+1]['metadata']):
        del dialog[idx]
    idx+=1

if len(dialog)==0 or len(dialog[-1]['metadata'])!=0:
    side = 'userside'
else:   side = 'systemside'

role     = {'userside':'a help desk client','systemside':'a help desk clerk'}
print """
    <img src="fig/cam.png" style="float:right;margin:10px;width:320px">
    <H2 style="padding-left:300px;padding-right:300px;text-align:center;">
        Role-play %s in a conversation
    </H2>
    <div class="tabber" id="mytab1">
    <div class="tabbertab">
    <h2>Introduction</h2>
    <div><img src="../mt-common/mturk-computer-headset.png" width="110" height="110" style="float:right;margin:15px;">
""" % (role[side])

if side=='userside':printUserSteps()
else:               printSysSteps()

print 'If this is your first time participating in this HIT, we suggest you go through <a href="javascript:document.getElementById(\'mytab1\').tabber.tabShow(1)">video tutorial</a>.<br>'
print 'Note: For each HIT, you only need to <span class="emphasis">provide your response for one turn</span>, not an entire conversation.<br>'
print 'Note: You will engage in a complete different conversation for each HIT. <span class="emphasis">Your role is changing all the time!</span><br>'
print 'Make sure your browser supports <span class="emphasis">pop-up dialogs</span>. You can reopen the webpage if you mistakenly prevent it from pop-up.<br>'
print"""
Please, submit at <span class="emphasis">least 10 HITs</span> in total, but <span class="emphasis">200 HITs maximum per day</span>. You are welcome to come the next day and do another 200 HITs.<br>
Please <span class="emphasis">do not submit more than 1000 HITs in total</span>.  You can bookmark the following <a
target="_top" href="https://www.mturk.com/mturk/searchbar?searchWords=restaurant+information"> link on MTURK search</a>.<br>
All data is collected anonymously and it will be used only for research purposes by <a href="http://mi.eng.cam.ac.uk/research/dialogue"> Dialogue Systems Group, Cambridge University Engineering Department</a>.
<p></p>
</div>
</div> <div class="tabbertab">
""" 
if side=='userside':
    include('util/woz-user-instructions.html')
else:
    include('util/woz-system-instructions.html')
print """
</div>
<div class="tabbertab">
"""

include('../mt-common/mturk-consent.html')
print """
</div>
</div>
"""

if assignmentId == 'ASSIGNMENT_ID_NOT_AVAILABLE':
    print """
        <div align="center">
        <div class=warning class="emphasis">
            This is a preview of the HIT. Accept the HIT before you chat to the service.
        </div>
        </div>
    """
    

### chat box & dialog history
dtexts = []
metadata = []
for i in range(len(dialog)):
    turn = dialog[i]
    speaker = 'Help Desk : ' if i%2==1 else 'Customer : '
    dtexts.append([speaker,turn['text'].replace('\n','')])
    metadata.append(turn['metadata'])
currentSpeaker = 'Help Desk : (<b>Your response</b>)' if side=='systemside' else 'Customer : (<b>Your response</b>)'

print """
<script src="//ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min.js"></script>
<script>
var side = "%s";
var count = 0;
var dialog = %s;
var taskfile = "%s";
var workerId = "%s";
var hitid = "%s";

//window.onbeforeunload = function (e) {
//    submitTurn(goal,{},taskID,workerId,hitId);
//}

function size_dict(d){c=0; for (i in d) ++c; return c}

function unlockResponse(animate=true){
    document.getElementById("token").disabled = false;
    document.getElementById("token").style.cursor= "pointer";
    document.getElementById("token").placeholder = 'your response :';
    document.getElementById("submitbutton").style.cursor = "pointer";
    document.getElementById("submitbutton").style.opacity= 1.0
    document.getElementById("submitbutton").disabled = false;
    if (side=="systemside"){
        document.getElementById("EOD").style.cursor = "pointer";
        document.getElementById("EOD").disabled = false;
    }
    if (animate){
        var h = $("#token").offset().top-500;
        $("html, body").animate({ scrollTop: h }, 500);
    }
}

function showTurn(widget){
    if(count>=dialog.length){
        swal({
            title:  "Info!",
            html:   "You have seen the entire dialogue.<br>Type in your response now!",
            type:   "info",
            confirmButtonColor: '#2B9DAB'
        }).catch(swal.noop);
        widget.disabled = true;
        widget.style.cursor = "not-allowed";
        widget.style.opacity= 0.5;
        unlockResponse();
        $(".tablinks").prop("disabled",false);
    }
    else{
        var speaker = dialog[count][0];
        var text = dialog[count][1]+"&nbsp;"
        if(count+1>=dialog.length){
            speaker = "<b>" + speaker + "</b>";
            text = "<b>" + text + "</b>";
        }
        // create dynamic table elements
        historyTable = document.getElementById("demo");
        var row = historyTable.insertRow();
        var cell1 = row.insertCell(0);
        var cell2 = row.insertCell(1);
        // Add some text to the new cells:
        cell1.innerHTML = speaker;
        cell2.innerHTML = text;
        cell1.classList.add('history');
        cell2.classList.add('history');
        cell1.setAttribute("style", "max-width:700px;");
        cell2.setAttribute("style", "max-width:700px;");
        count +=1;
        if(count>=dialog.length){
            widget.disabled = true;
            widget.style.cursor = "not-allowed";
            widget.style.opacity= 0.5;
            if(side=="userside"){
                swal({
                    title:  "Info!",
                    html:   "You have seen the entire dialogue.<br>Type in your response now!",
                    type:   "info",
                    confirmButtonColor: '#2B9DAB'
                }).catch(swal.noop); 

                unlockResponse();
            } else{
                swal({
                    title:  "Info!",
                    html:   "You have seen the entire dialogue.<br>Choose a domain and answer the questions!",
                    type:   "info",
                    confirmButtonColor: '#2B9DAB'
                }).catch(swal.noop); 
                $(".tablinks").prop("disabled",false);
                document.getElementById("token").placeholder = "you need to fill in the questionnaires above first.";
                document.getElementById("defaultButton").click();
                var h = $("#domainTab").offset().top-25;
                $("html, body").animate({ scrollTop: h }, 500);
            }
        }
    }
}


function actualSubmit(){

    swal({
        title:  "Are you sure?",
        html:   "Unthoughtful submissions will be automatically rejected.",
        type: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#2B9DAB',
        cancelButtonColor: '#e69000',
        confirmButtonText: 'Yes, submit it!'
    }).then(function () {
        
        document.getElementById("submitbutton").disabled=true; 
        var thisturn = {"text":document.getElementById("token").value,"metadata":{}};
        if(side=="systemside"){
            // init metadata information 
            domains = ['restaurant','hotel','attraction','hospital','train','taxi','police'];
            for(var d=0;d<domains.length;d++){
                thisturn['metadata'][domains[d]] = {'semi':{},'book':{}};
                thisturn['metadata'][domains[d]]['semi'] = window[domains[d]+'_semi'];
                thisturn['metadata'][domains[d]]['book'] = window[domains[d]+'_book'];
            } // update semi information from questionnaires
            for(var d=0;d<domains.length;d++){
                for(var i=0;i<=6;i++){
                    var tid = domains[d]+'_informable'+i.toString();
                    var wgt = document.getElementById(tid);
                    if (wgt!=null){
                        thisturn["metadata"][domains[d]]['semi'][wgt.name] = wgt.value;
                    }
                }
            } // update booking info
            for(var d=0;d<domains.length;d++){
                for(var i=0;i<=2;i++){
                    var tid = domains[d]+'_book'+i.toString();
                    var wgt = document.getElementById(tid);
                    if (wgt!=null){
                        thisturn["metadata"][domains[d]]["book"][wgt.name] = wgt.value;
                    }
                }
            }
        }
        if(side=='userside'){
            goal['messageLen'] = msgLen+1;
        } else {
            var eod = document.getElementById("EOD").checked;
            goal['eod'] = eod;
        }
        submitTurn(goal,thisturn,taskID,workerId,hitId,assignmentId);

        swal({
            title:  "Submitted!",
            html:   "Your task has been submitted!",
            type:   "success",
            confirmButtonColor: '#2B9DAB',
            timer:  1000}).catch(swal.noop);
    }).catch(swal.noop);
}

function mysubmit(){
    var response = document.getElementById("token").value;
    if(response==''){
        swal({
            title:  "Warning!",
            html:   "You should type in your response.",
            type:   "warning",
            confirmButtonColor: '#2B9DAB'
        }).catch(swal.noop); 
        return false;
    
    } else if(response.split(" ").length<3){
        swal({
            title:  "Warning!",
            html:   "The response is too short.<br>Too many unthoughtful submissions will result in account being banned from this HIT.",
            type:   "error",
            confirmButtonColor: '#2B9DAB'
        }).catch(swal.noop); 
        return false;
    } else {
        
        // check goodbye
        var response = document.getElementById("token").value.toLowerCase();
        if (dialog.length==0){
            var request = "";
        } else {
            var request  = dialog[dialog.length-1][1].toLowerCase();
        }
        var signs = ['goodbye','bye'];
        var suggestFinish = false;
        for (var i=0;i<signs.length;i++){
            if ( response.indexOf(signs[i])!=-1|| request.indexOf(signs[i])!=-1)
                suggestFinish = true;
        }
        if (suggestFinish==true && side=="systemside"){
            var checkbox = document.getElementById("EOD")
            swal({
                title:  "Is the dialogue finished?",
                html:   "Is the user satistified?<br>Have all the requests been done?",
                type:   "question",
                showCancelButton:   true,
                confirmButtonColor: '#2B9DAB',
                cancelButtonColor:  '#e69000',
                confirmButtonText:  'Yes, it does!',
                cancelButtonText:   'No, not yet!'
            }).then(function () {
                checkbox.checked = true;    
                actualSubmit(); 
            }, function (dismiss){
                if (dismiss=="cancel"){
                    checkbox.checked = false;
                    actualSubmit(); 
                }
            })
        } else {
            actualSubmit(); 
        }
        return true;
    }
}
function keypress(e){
    if(e.keyCode == 13){
        swal({
            title:  "Info!",
            html:   "Click the submit button to submit your task!",
            type:   "info",
            confirmButtonColor: '#2B9DAB'
        }).catch(swal.noop);
        return false;
    } else{
        return true;
    }
}
function endOfDialogue(checkbox,e){
    if(!checkbox.checked){
        return true;
    }
    swal({
        title:  "Time to end?", 
        html:   "Is your client satisfied?<br>Is it time to end this conversation?",
        type: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#2B9DAB',
        cancelButtonColor: '#e69000',
        confirmButtonText: 'Yes, it is finished!'
    }).then(function () {
        checkbox.checked = true;    
    }, function (dismiss){
        checkbox.checked = false;
    });
}
function textCounter(field,field2,maxlimit){

    var countfield = document.getElementById(field2);
    if ( field.value.split(" ").length > maxlimit ) {
        countfield.style.border = "1px solid #ff0000";
        field.style.border = "1px solid #ff0000";
        countfield.style.color = "red";
        countfield.value = "invalid";
    } else {
        countfield.style.border = "0px";
        field.style.border = "1px solid #737373";
        countfield.value = maxlimit - field.value.split(" ").length;
        countfield.style.color = "black";
    }
}
</script>
""" % (side,json.dumps(dtexts),taskfile,workerId,hitId)#,showComplete)

######################################################################## 
######################### USER SIDE CODE ###############################
######################################################################## 
if side=='userside':
    print """
        <div class="task" style="float:right">
            <p><strong>Please try to chat about the following topic: </strong></p>
            <strong>Task %(taskID)s:</strong><br>
            %(task)s
        </div>""" % {'taskID':taskID,'task':taskMsg}

percent = '55%' if side=='userside' else '100%'
print """
<div class=chatbox style="float:left;width:%s">""" % percent
if side=='systemside':
    print"<div><strong>Task %s</strong></div><p></p>" % taskID
print """
<table id="demo"><tbody>
    <tr><td class="history" style="width:%s">Help Desk:&nbsp;</td>
    <td class="history" style="max-width:%s">Hello, welcome to the Cambridge TownInfo centre. I can help you find a restaurant or hotel, look for tourist information, book a train or taxi. How may I help you ?</td></tr>
</tbody></table>
<p></p>
<button type="button" class='button submit' onclick="showTurn(this)">Next turn</button>
<p></p>
"""% ('120px','65%')


default_meta = {}
required_slots = {
    'restaurant': ['food','area','pricerange','name'],
    'hotel': ['type','area','pricerange','stars','internet','parking','name'],
    'attraction': ['type','area','name'],
    'hospital': ['department'],
    'taxi': ['departure','destination','leaveAt','arriveBy'],
    'train': ['departure','destination','day','leaveAt','arriveBy'],
    'police': []
}
book_slots = {
    'restaurant':   ['day','time','people'],
    'hotel':        ['day','stay','people'],
    'attraction':   [],
    'hospital':     [],
    'taxi':         [],
    'train':        ['people'],
    'police':       []
}
for d in ['restaurant','hotel','attraction','hospital','police','train','taxi']:
    default_meta[d] = {'semi':{},'book':{'booked':[]}}
    for s in required_slots[d]:
        default_meta[d]['semi'][s] = ''
    for s in book_slots[d]:
        default_meta[d]['book'][s] = ''

printDefaultSuggestedValues()
if side=='systemside':
    # last tracker info
    meta = metadata[-2] if len(metadata)>2 else default_meta
    # load all datasets
    db, s2v = loadDatasets()
    # print all meta data
    printMetadata(meta,s2v)
    # print tab
    printImportedScript()
    printTab()
    # print domain tabs
    printRestaurantTab( meta['restaurant'], db['restaurant'], s2v['restaurant'] )
    printHotelTab(      meta['hotel'],      db['hotel']     , s2v['hotel']      )
    printAttactionTab(  meta['attraction'], db['attraction'], s2v['attraction'] )
    printHospitalTab(   meta['hospital'],   db['hospital'],   s2v['hospital']   )
    printPoliceTab(     meta['police']      )
    printTrainTab(      meta['train'],      db['train'],      s2v['train']      )
    printTaxiTab(       meta['taxi'],       db['taxi'],       s2v['taxi']       )
    printDefaultTab()

print """<div><form id="form">
<p>%s</p>
<textarea id="token" name="token" class="textfield" rows="3" cols="70" required autocomplete="off" style="cursor: not-allowed" disabled placeholder="you need to go through the dialogue first by clicking the 'next turn' button" onkeypress="return keypress(event)" onkeyup="textCounter(this,'counter',31);"></textarea>""" % (currentSpeaker)

print """<input disabled maxlength="5" size="5" value="30" id="counter" style="font-size:16px;border:0px;background-color:#DBE8ED">"""
if side=='systemside':
    print '<p><input type="checkbox" name="EOD" id="EOD" style="cursor: not-allowed" onclick="endOfDialogue(this,event)" disabled>&nbsp;&nbsp;end-of-dialogue?</p>'
print """
<p></p>
<button type="button" name="submitbutton" class="button submit disabled" onclick="mysubmit();" id="submitbutton" disabled>Submit the HIT</button></div>
</div>
"""

if assignmentId == "ASSIGNMENT_ID_NOT_AVAILABLE":
    print """<script>disableToken();</script>"""

# footer
print """
<div id="footer" style="width:95%">
<center>Posted by: Dialogue Systems Group</center>
<center>Contact: dialoguesystems@gmail.com</center>
</div>
"""

print """
    </BODY>
</HTML>
""" 
