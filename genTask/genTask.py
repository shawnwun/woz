######################################################################
######################################################################
#  Copyright Tsung-Hsien Wen, Cambridge Dialogue Systems Group, 2017 #
######################################################################
######################################################################
import os
import sys
import operator
import random
import json
from generator import *
from copy import deepcopy

requestable_slots = {
    'restaurant':   ['name','food','area','pricerange','phone','postcode','address'],
    'hotel':        ['name','type','area','pricerange','stars','internet','parking',
                    'phone','postcode','address'],
    'attraction':   ['name','type','area','phone','postcode','address','entrance fee'],
    'hospital':     ['department','phone'],
    'taxi':         ['departure','destination','leaveAt','arriveBy'],
    'train':        ['trainID','departure','destination','day','leaveAt','arriveBy','price','duration']
}
constraint_slots = {
    'restaurant':   ['food','area','pricerange'],
    'hotel':        ['type','area','pricerange','stars','internet','parking'],
    'attraction':   ['type','area'],
    'hospital':     ['department'],
    'taxi':         ['departure','destination','leaveAt','arriveBy'],
    'train':        ['departure','destination','day','leaveAt','arriveBy']
}

booking_slots = {
    'restaurant':   ['day','time','people'],
    'hotel':        ['day','stay','people'],
    'attraction':   [],
    'hospital':     [],
    'taxi':         [],
    'train':        ['people'],
    'police':       []
}

scenarios = {
    'restaurant': {
        'find': [
            "You are also looking for a <span class='emphasis'>place to dine</span>",
            "You are also looking for a <span class='emphasis'>restaurant</span>"
        ],
        'byname': [
            "You are also looking for a <span class='emphasis'>particular restaurant</span>"  
        ]
    },
    'hotel': {
        'find': [
            "You are also looking for a <span class='emphasis'>place to stay</span>"
        ],
        'byname': [
            "You are also looking for a <span class='emphasis'>particular hotel</span>"
        ]
    },
    'attraction': {
        'find': [
            "You are also looking for <span class='emphasis'>places to go</span> in town"
        ],
        'byname': [
            "You are also looking for a <span class='emphasis'>particular attraction</span>"
        ]
    },
    'hospital': {
        'find': [
            "You got injured and are looking for a <span class='emphasis'>hospital</span> nearby",
            "You want to find a <span class='emphasis'>hospital</span> in town",
            "You are looking for the <span class='emphasis'>Addenbrookes Hospital</span>"
        ]
    },
    'police': {
        'find': [
            "You were <span class='emphasis'>robbed</span> and are looking for help",
            "You were in a <span class='emphasis'>car accident dispute</span> and are looking for help",
            "You are looking for the nearest <span class='emphasis'>police station</span>",
            "You are looking for the Parkside <span class='emphasis'>Police Station</span>"
        ]
    },
    'train': {
        'to': [
            "You are also looking for a <span class='emphasis'>train</span>"
        ],
        'from': [
            "You are also looking for a <span class='emphasis'>train</span>"
        ]
    },
    'taxi': {
        'to': [
            "You also want to book a <span class='emphasis'>taxi</span>"    
        ],
        'from': [
            "You also want to book a <span class='emphasis'>taxi</span>"
        ]
    }
}

multi_scenarios = {
    ('hotel','restaurant'):[
        'You are traveling to Cambridge and looking forward to try local restaurants',
        'You are looking for information in Cambridge',
        'You are planning your trip in Cambridge'
    ],    
    ('attraction','restaurant'):[
        'You are traveling to Cambridge and excited about seeing local tourist attractions',
        'You are traveling to Cambridge and looking forward to try local restaurants',
        'You are looking for information in Cambridge',
        'You are planning your trip in Cambridge'
    ],    
    ('restaurant','train'):[
        'You are traveling to Cambridge and looking forward to try local restaurants',
        'You are looking for information in Cambridge',
        'You are planning your trip in Cambridge'
    ],    
    ('attraction','hotel'):[
        'You are traveling to Cambridge and excited about seeing local tourist attractions',
        'You are looking for information in Cambridge',
        'You are planning your trip in Cambridge'
    ],    
    ('hotel','train'):[
        'You are looking for information in Cambridge',
        'You are planning your trip in Cambridge'
    ],    
    ('attraction','train'):[
        'You are looking for information in Cambridge',
        'You are planning your trip in Cambridge'
    ] 
}


pois = set(['addenbrookes hospital','parkside police station'])
hours = ['0'+str(i) for i in range(8,10)] + [str(i) for i in range(10,22)]
openingHours = [str(i) for i in range(10,21)]
hours24 = ['0'+str(i) for i in range(1,10)] + [str(i) for i in range(10,25)]
mins_quater = ['00','15','30','45']

timeNormal = []
for h in hours:
    for m in mins_quater:
        timeNormal.append(h+':'+m)
trainTime = timeNormal

taxiTime = []
for h in hours24:
    for m in mins_quater:
        taxiTime.append(h+':'+m)

timeWork = []
for h in openingHours:
    for m in mins_quater:
        timeWork.append(h+':'+m)
timeWork.append('21:00')

week = ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']

stays = [str(i) for i in range(2,6)]
ppl   = [str(i) for i in range(1,9)]

book_values = {
    ('restaurant','day'): week,
    ('restaurant','people'): ppl,
    ('restaurant','time'): timeWork,
    ('hotel','day'): week,
    ('hotel','stay'): stays,
    ('hotel','people'): ppl,
    ('train','people'): ppl
}


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
            s2v['day'] = week
            s2v['departure'].remove('cambridge')
            s2v['destination'].remove('cambridge')
        elif domain=='taxi':
            s2v['arriveBy']= taxiTime
            s2v['leaveAt'] = taxiTime
            s2v['destination'] = sorted(list(pois))
            s2v['departure'] = sorted(list(pois))
    return DB, S2V


def loadDOM(domain):
   
    # loading db and s2v files
    fin = file('../ontology/'+domain+'_db.json')
    db = json.load(fin)
    fin.close()
    fin = file('../ontology/'+domain+'_s2v.json')
    s2v = json.load(fin)
    fin.close()    
    # accumulate informable slot values from both file and db
    for e in db:
        for s in requestable_slots[domain]:
            if e.has_key(s) and s2v.has_key(s):
                s2v[s].append(e[s])
    # adding requestable slots
    for s in requestable_slots[domain]:
        if not s2v.has_key(s): s2v[s] = []
    # add special values to s2v
    for s,vs in s2v.iteritems():
        if len(vs)!=0:
            if s=='departure' or s=='destination':
                s2v[s] = sorted(list(set(vs)))
            else:
                s2v[s] = sorted(list(set(vs)))
    # adding POIs
    if domain=='restaurant' or domain=='hotel' or domain=='attraction' or domain=='train':
        for e in db:
            for s in requestable_slots[domain]:
                if s=='name':
                    pois.add(e[s])
                if s=='departure':
                    pois.add(e[s]+' train station')
    return db, s2v


def checkMatch(db,info_slots):

    match = []
    for entry in db:
        isMatch = True
        for s,v in info_slots.iteritems():
            if v=='': continue
            if s in entry:
                if s=='arriveBy':
                    if entry[s]>v: isMatch=False
                    if entry[s]<'05:00': isMatch=False
                elif s=='leaveAt':
                    if entry[s]<v: isMatch=False
                elif entry[s]!=v:
                    isMatch=False
            else: 
                isMatch = False
        if isMatch: match.append(entry)
    return match


def get_requestables(domain, info_slots):
    # special domains
    default = ['postcode','address','phone']
    random.shuffle(default)
    ni = random.randint(1,3)
    if domain=='taxi':
        return ['car type','contact number']
    if domain=='police':
        return default[:ni]
    if domain=='hospital':
        return default[:ni]
            
    # the others
    ni = random.randint(1,3)
    slots = requestable_slots[domain][1:] \
            if domain in ['restaurant','hotel','attraction','hospital'] \
            else requestable_slots[domain]
    random.shuffle(slots)
    reqt_slots = []
    for s in slots:
        if s not in info_slots:
            reqt_slots.append(s)
        if len(reqt_slots)>=ni:
            break
    return reqt_slots

def filterTime(times,t,later=True,gap=-1):
    filtered_times = []
    for ti in times:
        if later and ti>t:
            if gap!=-1:
                hi= int(ti.split(':')[0])
                h = int(t.split(':')[0])
                if hi-gap>h:
                    filtered_times.append(ti)
            else:
                filtered_times.append(ti)
        elif not later and ti<t:
            if gap!=-1:
                hi= int(ti.split(':')[0])
                h = int(t.split(':')[0])
                if hi+gap<h:
                    filtered_times.append(ti)
            else:
                filtered_times.append(ti)
    return filtered_times

def get_bookables(domain,prevDomainInfo):
    book_slots = {}
    
    if len(booking_slots[domain])!=0:
        for s in booking_slots[domain]:
            if s in prevDomainInfo['book']:
                # init value from previous domain and filter entity
                book_slots[s] = prevDomainInfo['book'][s]
            elif s in prevDomainInfo['info']:
                book_slots[s] = prevDomainInfo['info'][s]
            else: # no match
                if s=='time' and ('arriveBy' in prevDomainInfo['info'] or 
                                'leaveAt' in prevDomainInfo['info']): 
                    # if slot==time, check arriveBy and leaveAt
                    trainT = prevDomainInfo['info']['arriveBy'] if 'arriveBy' in prevDomainInfo['info']\
                            else prevDomainInfo['info']['leaveAt']
                    if prevDomainInfo['task']=='to': # arriving cambridge, make sure table after leaving
                        book_slots['time'] = random.choice(
                                filterTime(timeWork,trainT,later=True,gap=2))
                    else: # leaving cambrdige, make sure table booked before leaving
                        book_slots['time'] = random.choice(
                                filterTime(timeWork,trainT,later=False,gap=2))
                else: # other cases
                    # random choose a value 
                    if (domain,s)==('restaurant','time'):
                        vals = book_values[(domain,s)][4:-4]
                    else:
                        vals = book_values[(domain,s)]
                    book_slots[s] = random.choice(vals)
        
        # special case
        if domain=='hotel' and prevDomainInfo['task']=='from': # leaving cambridge
            book_slots['day'] = week[(week.index(prevDomainInfo['info']['day'])-int(book_slots['stay']))%7]
        # for simulating invalid bookings
        if random.uniform(0,1)>0.5:
            book_slots['invalid'] = True
        else:
            book_slots['invalid'] = False
        return book_slots


db,s2v = loadDatasets()
lowerbound = {
    'restaurant':2,
    'hotel':3,
    'attraction':1
}

def get_informables(domain,task,prevDomainInfo):

    # special domains
    if domain=='police': return {},{},{}
    if domain=='hospital':
        if random.uniform(0,1)>0.5: return {},{},{}
        else: return {'department':random.choice(s2v[domain]['department'])},{},{}

    # for different tasks, assign different slots
    if task=='find': # by slot-value pairs
        ni = random.randint(lowerbound[domain],min(len(constraint_slots[domain]),4))
        slots = constraint_slots[domain]
        random.shuffle(slots)
        info_slots = dict([(s,'')for s in slots[:ni]])
    elif task=='byname': # by name, the slot is 'name'
        info_slots = {'name':''}
    elif task=='from' or task=='to':
        info_slots = {'departure':'','destination':''}
        # train specific operation
        if domain=='train': 
            # departure and destination
            if task=='from':
                info_slots['departure']  = 'cambridge' 
                info_slots['destination']= random.choice(s2v[domain]['destination'])
            elif task=='to':  
                info_slots['departure']  = random.choice(s2v[domain]['departure'])
                info_slots['destination']= 'cambridge' 
            
            # adding day for booking
            if prevDomainInfo['book'].has_key('day'): # only happens for restaurant & hotel domains
                if task=='from': # leaving cambridge
                    if prevDomainInfo['domain']=='hotel': # make sure it leaves after the hotel booking
                        dayIdx = (week.index(prevDomainInfo['book']['day'])+int(prevDomainInfo['book']['stay']))%7
                        info_slots['day'] = week[dayIdx]
                    elif prevDomainInfo['domain']=='restaurant': # make sure it leaves after the restaurant booking : the other day
                        info_slots['day'] = week[(week.index(prevDomainInfo['book']['day'])+1)%7]
                else: # arriving cambridge
                    if prevDomainInfo['domain'] =='hotel': # make sure it arrives on the same day
                        info_slots['day'] = prevDomainInfo['book']['day']
                    elif prevDomainInfo['domain']=='restaurant': # make sure it arrives before the restaurant booking
                        info_slots['day'] = prevDomainInfo['book']['day']
                        info_slots['arriveBy'] = random.choice( 
                                filterTime(trainTime,prevDomainInfo['book']['time'],later=False,gap=2))
            else: # other cases, randomly choose one
                info_slots['day'] = random.choice(week)
          
            # choose leave at or arrive by
            if 'arriveBy' not in info_slots:
                if random.uniform(0,1)>0.5:
                    info_slots['leaveAt']    = random.choice(trainTime)
                else:
                    info_slots['arriveBy']   = random.choice(trainTime)
          
            # reiterate to make sure always find a train
            while len(checkMatch(db[domain],info_slots))<=0:
                if 'leaveAt' in info_slots:
                    info_slots['leaveAt'] = random.choice(trainTime)
                else:
                    if 'time' in prevDomainInfo['book']:
                        info_slots['arriveBy'] = random.choice(
                                filterTime(trainTime,prevDomainInfo['book']['time'],later=False,gap=2))
                    else:
                        info_slots['arriveBy']= random.choice(trainTime)

            return info_slots, {},{}
        else: # taxi
            random.shuffle(s2v[domain]['destination'])
            info_slots['departure']  = s2v[domain]['destination'][0]
            info_slots['destination']= s2v[domain]['destination'][1]
            # choose leave at or arrive by
            if random.uniform(0,1)>0.5:
                info_slots['leaveAt']    = random.choice(taxiTime)
            else:
                info_slots['arriveBy']   = random.choice(taxiTime)
            return info_slots, {},{}

    # init value from previous domain and filter entity
    for s in prevDomainInfo['info'].iterkeys():
        if s in info_slots:
            info_slots[s] = prevDomainInfo['info'][s]
    # filter entites
    entities = checkMatch(db[domain],info_slots)

    if len(entities)==0:
        # if the db doesn't have matching entities
        entities = db[domain]
        # reset informable slots
        for s in info_slots: info_slots[s] = ''

    # choose other values directly from one of the entity
    entity = random.choice(entities)
    for s in info_slots.iterkeys():
        info_slots[s] = entity[s]         
    
    # toss a coin to decide scenarios -> invalid+valid, valid 
    changed_slots = {}
    swt = random.uniform(0,1)
    if swt>0.35:
        none_matched_slots = {}
    else:
        none_matched_slots = deepcopy(info_slots)
        # generate the non-matched slot-value pairs
        isFound = False
        for s in info_slots.iterkeys():
            valarr = s2v[domain][s]
            random.shuffle(valarr)
            for v in valarr:
                none_matched_slots[s] = v
                if len(checkMatch(db[domain],none_matched_slots))==0:
                    changed_slots[s] = info_slots[s]
                    isFound = True
                    break
            if isFound:
                break
    
    return info_slots, changed_slots, none_matched_slots 



bookRatio = {
    'hospital': 0.5, 
    'police':   0, 
    'taxi':     0, 
    'train':    0.5, 
    #'train': 1,
    #'restaurant': 1,
    'restaurant':0.66, 
    'hotel':    0.66, 
    'attraction':0
}


def singleDomainSlotValues(domain, prevDomainInfo):

    # define task = find/byname
    task = 'find' if random.uniform(0,1)>0.2 else 'byname'
    if domain in ['train','taxi']: task = random.choice(['from','to'])
    if domain in ['police','hospital']: task = 'find'

    # choose the informable slots
    info_slots, changed_slots, none_matched_slots = get_informables(domain,task,prevDomainInfo)
    # choose the requestable slots 
    reqt_slots = get_requestables(domain,info_slots)
    # choose the booking slots
    book_slots = get_bookables(domain,prevDomainInfo)

    return task, info_slots, changed_slots, none_matched_slots, reqt_slots, book_slots


def singleDomainMessage(domain, task, info_slots, changed_slots, none_matched_slots, 
        reqt_slots, book_slots, prevDomainInfo):
    # check whether there is a match
    if domain in ['taxi','police','hospital']: m=-1
    else: m = len(checkMatch(db[domain],none_matched_slots))

    # record task path
    path = []

    # generate task message
    msg = []
    msg.append(random.choice(scenarios[domain][task])) # scenario
    # generate message for informable slots
    if len(info_slots)!=0:
        if m==0: # if the first search is invalid
            msg.extend( inform_generator(none_matched_slots,domain,prevDomainInfo) )
            msg.extend( inform_alter_generator(changed_slots,domain) )
            path.extend(['invalid','alter'])
        elif task=='byname': # search by name
            msg.append( inform_name_generator(info_slots,domain) )
            path.append('byname')
        else: # general case, search by slot-value pairs
            msg.extend( inform_generator(info_slots,domain,prevDomainInfo) )
            path.append('inform')

    book_fail_sv = ()
    if domain in ['restaurant','hospital','hotel','train']:
        swt = random.uniform(0,1)
        # special hospital domain
        if domain=='hospital' and len(info_slots)==0:
            msg.append( request_generator(reqt_slots,domain) )
            path.append('request')
        # bookable domains
        elif swt<bookRatio[domain]: # booking 
            book_msg, book_fail_sv = book_generator(book_slots,domain,prevDomainInfo)
            msg.extend( book_msg )
            path.append('book')
        else: # just request
            msg.append( request_generator(reqt_slots,domain) )
            path.append('request')
    else:# not bookable domains, always request 
        msg.append( request_generator(reqt_slots,domain) )
        path.append('request')

    # merge the front two sentences except for police and hospital domains
    if len(msg)>2:
        msg = [msg[0]+'. '+msg[1]] + msg[2:]

    return msg,path,book_fail_sv


taskType = sys.argv[1]

taskList = []
sampleRatio = 1#0.025


if taskType=='multi':
    # multi-domain tasks
    multidomains = [
        ('hotel','restaurant'),
        ('restaurant','train'),
        ('attraction','train'),
        ('hotel','train'),
        ('attraction','restaurant'),
        ('attraction','hotel')
    ]

    numOfTasks = [
        200,
        300,
        300,
        300,
        200,
        200
    ]

    ID = 1200
    for d in range(len(multidomains)):
        N = numOfTasks[d]
        i = 0
        while i<N:
            try:
                goal = {'hotel':{},'restaurant':{},'attraction':{},'train':{},
                        'hospital':{},'police':{},'taxi':{},'messageLen':2}

                # global message
                msgs = []
                msgs.append(random.choice(multi_scenarios[multidomains[d]])) 
                # shuffle domains
                domains = list(multidomains[d])
                random.shuffle(domains)
                prevInfo = {'info':{},'book':{},'reqt':{},'domain':'','task':''}
                restBooked = ''
                for j in range(len(domains)):
                    domain = domains[j]
                    # generate slot values 
                    task, info_slots, changed_slots, none_matched_slots, reqt_slots, book_slots = \
                            singleDomainSlotValues(domain, prevInfo)
                    # generate message
                    msg,path,book_fail_sv = singleDomainMessage(domain, 
                            task, info_slots, changed_slots, none_matched_slots, 
                            reqt_slots, book_slots, prevInfo)
                    if j==0:
                        msg[0] = msg[0].replace('also ','')
                    msgs.extend(msg)

                    # insert domain info
                    prevInfo['info'] = info_slots
                    goal[domain]['info'] = info_slots
                    goal[domain]['fail_info'] = none_matched_slots
                    if 'book' in path:      
                        prevInfo['book'] = book_slots
                        goal[domain]['book'] = book_slots
                        goal[domain]['fail_book'] = book_fail_sv
                    if 'request' in path:
                        prevInfo['reqt'] = reqt_slots
                        goal[domain]['reqt'] = reqt_slots
                    prevInfo['domain'] = domain
                    prevInfo['task'] = task
                    # remember if a restaurant is booked
                    if domain=='restaurant' and 'book' in path:
                        restBooked = book_slots['time']

                # adding taxi domain
                if random.uniform(0,1)>0.5 and 'train' not in domains: # adding taxi domain
                    # taxi slot and message
                    if restBooked!='':
                        middle = 'You want to make sure it arrives the restaurant <span class=\'emphasis\'>by the booked time</span>' 
                        slots = {'arriveBy':restBooked}
                    else: 
                        t = random.choice(taxiTime)
                        middle = 'You want to leave the <span class=\'emphasis\'>%s</span> by <span class=\'emphasis\'>%s</span>' % (random.choice(domains),t)
                        slots = {'leaveAt':t} 
                    # taxi message
                    msgs.extend([
                        'You also want to book a <span class=\'emphasis\'>taxi</span> to commute between the two places',
                        middle,
                        'Make sure you get <span class=\'emphasis\'>contact number</span> and <span class=\'emphasis\'>car type</span>' ])
                    goal['taxi'] = {'info':slots,'reqt':['contact number','car type'],"fail_info": {}}

                # add message
                goal['message'] = msgs
                dialog = {'goal':goal,'log':[]}
                i+=1
                ID +=1
                
                # output task file
                fname = 'tasks/MUL%04d.json'%ID
                #print fname
                # sample task
                if random.uniform(0,1)<sampleRatio:
                    taskList.append(fname.split('/')[-1])
                    
                #print fname
                fout = file(fname,'w')
                fout.write(json.dumps(dialog, sort_keys=True,indent=4, separators=(',', ': ')))
                fout.close()
            except:
                pass

if taskType=='single':
    # single domain task : restaurant/hotel/attraction only
    # generate tasks for each domain
    domains = ['taxi','police','hospital','train','restaurant','hotel','attraction']
    numOfTasks=  [100, 50, 100, 200, 300, 300, 100]

    ID = 0
    for d in range(len(domains)):
        domain = domains[d]
        num = numOfTasks[d]
        ratio = bookRatio[domain]
        n = 0
        while n<num:
            try:
                goal = {'hotel':{},'restaurant':{},'attraction':{},'train':{},
                        'hospital':{},'police':{},'taxi':{},'messageLen':1}

                prevInfo = {'info':{},'book':{},'reqt':{},'domain':'','task':''}
                task, info_slots, changed_slots, none_matched_slots, reqt_slots, book_slots = \
                        singleDomainSlotValues(domain, prevInfo)
                # generate message
                msg,path,book_fail_sv = singleDomainMessage(domain, 
                        task, info_slots, changed_slots, none_matched_slots, 
                        reqt_slots, book_slots, prevInfo)
                msg[0] = msg[0].replace('also ','')

                goal['message'] = msg
                goal[domain]['info'] = info_slots
                goal[domain]['fail_info'] = none_matched_slots
                if 'book' in path:      
                    goal[domain]['book'] = book_slots
                    goal[domain]['fail_book'] = book_fail_sv
                if 'request' in path:
                    goal[domain]['reqt'] = reqt_slots
               
                # output task file
                n+=1
                ID +=1
                dialog = {'goal':goal,'log':[]}
                fname = 'tasks/SNG%04d.json'% ID
                #print fname
                if random.uniform(0,1)<sampleRatio:
                    taskList.append(fname.split('/')[-1])
                 
                #print fname
                fout = file(fname,'w')
                fout.write(json.dumps(dialog, sort_keys=True,indent=4, separators=(',', ': ')))
                fout.close()
            except:
                pass
            #print '.\n'.join(msg)
            #print
        #raw_input()
print '\n'.join(taskList)
