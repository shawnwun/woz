######################################################################
######################################################################
#  Copyright Tsung-Hsien Wen, Cambridge Dialogue Systems Group, 2017 #
######################################################################
######################################################################

#! /usr/bin/python
# -*- coding: utf-8 -*-

__author__="Filip Jurcicek"
__date__ ="$08-Mar-2010 13:45:34$"

import cgi
import cgitb
import os.path
import os
import time
import sys
import json
if '' not in sys.path:
    sys.path.append('')
from utils import *

def getWorkerID(xmlFeedback):
    i = xmlFeedback.find("<workerId>")
    ii = xmlFeedback.find("</workerId>")
    if i != -1 and ii != -1:
        id = xmlFeedback[i+len("<workerId>"):ii].strip()
        return id

    return ""

print "Content-type: text/html\n\n"
cgitb.enable()

form = cgi.FieldStorage()

#for k in form:
#    print "Variable:", k , "Value:", form[k].value
#print

turn = json.loads(form.getfirst('turnLog','None'))
goal = json.loads(form.getfirst('mgoal','None'))
filename = form.getfirst('taskIdentifier','None')+'.json'
workerid = form.getfirst('worker','None')
assignmentId = form.getfirst('assignmentId','None')
hitId = form.getfirst('hit','None')
#workerId = form.getfirst('wkid','None')
#if tokenTuple:

# save the dialogue locally
#print "Worker "+workerId
#f = file('newdata/tv/log_'+str(dialogue['taskID'])+'_'+str(time.time())+'.txt','w')

# update taskIDs
from lockfile import LockFile
lock = LockFile('lock/tasks.lock')
with lock:
    listFile = 'lock/taskList' #if not showComplete else 'tmp/finishedList'
    fin = file(listFile)
    # read index
    currentIdx = int(fin.readline().replace('\n',''))
    # read taskIDs
    tasks = [x.replace('\n','') for x in fin.readlines()]
    fin.close()
    
    # save this turn into log file
    fin = file('tempTasks/'+filename)
    data = json.load(fin)
    fin.close()
    # if turn >0, append it
    if len(turn)>0:
        turn['workerid']= workerid
        turn['hidid']   = hitId
        turn['assignmentid'] = assignmentId
        data['log'].append(turn)
    # set goal
    data['goal'] = goal
    # write it back to file
    fout= file('tempTasks/'+filename,'w')
    fout.write(json.dumps(data,sort_keys=True,indent=4, separators=(',', ': ')))
    fout.close()
    
    # remove task if end-of-dialogue
    eod = data['goal']['eod'] if 'eod' in data['goal'] else False
    if eod:
        tasks.remove(filename)
        currentIdx -= 1
    
    # write back the lock count file
    fout = file(listFile,'w')
    fout.write('\n'.join([str(currentIdx)]+tasks))
    fout.close()

