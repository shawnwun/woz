######################################################################
######################################################################
#  Copyright Tsung-Hsien Wen, Cambridge Dialogue Systems Group, 2017 #
######################################################################
######################################################################
import sys
import os
import operator
import json
import numpy as np

files = sorted(os.listdir('tempTasks'))
"""
fin = file('lock/taskList')
files = [line.replace('\n','') for line in fin.readlines()]
fin.close()
"""

workers = {}

for f in files[1:]:
    fin = file('tempTasks/'+f)
    task = json.load(fin)
    fin.close()
    
    for l in task['log']:
        if l['workerid'] in workers:
            workers[l['workerid']].append({'hidid':l['hidid'],'text':l['text']})
        else:
            workers[l['workerid']] = [{'hidid':l['hidid'],'text':l['text']}]

HITPerWorker = np.array([len(workers[worker]) for worker in workers])
totalHITs = np.sum(HITPerWorker)

#print sorted([len(workers[worker]) for worker in workers])
"""
for worker, msgs in workers.iteritems():
    toprint = False
    for msg in msgs:
        if len(msg['text'].split())<=3: 
            toprint = True
            print msg['text']
    if toprint:
        raw_input()
"""
for worker, msgs in sorted(workers.items(),key=lambda x:len(x[1])):
    texts = [m['text'] for m in msgs]
    print worker, len(texts)

    
    
print '# of workers:    %d' % len(workers)
print '# of turns:      %d' % totalHITs
print 'avg HITs/worker: %.1f, %.1f' % (np.mean(HITPerWorker),np.std(HITPerWorker))

