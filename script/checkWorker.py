######################################################################
######################################################################
#  Copyright Tsung-Hsien Wen, Cambridge Dialogue Systems Group, 2017 #
######################################################################
######################################################################
import sys
import os
import operator
import json


files = sorted(os.listdir('tempTasks'))
"""
fin = file('lock/taskList')
files = [line.replace('\n','') for line in fin.readlines()]
fin.close()
"""
workerid = sys.argv[2]
stop = sys.argv[1]

cnt = 0
for f in files[1:]:
    if stop=='true':
        print f
    fin = file('tempTasks/'+f)
    task = json.load(fin)
    fin.close()
    for l in task['log']:
        if l['workerid']==workerid:
            cnt +=1
            if stop=='true':
                print l['text']+'\n'
                print l['hidid']
                raw_input()
            else:
                print l['hidid']
        else: 
            if stop=='true':
                print l['text']
    if stop=='true':
        print

print cnt
