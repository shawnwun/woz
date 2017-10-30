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

    i = 0
    changed = False
    while i<len(task['log'])-1:
        if len(task['log'][i]['metadata'])==len(task['log'][i+1]['metadata']):
            for j in range(max(i-1,0),min(i+2,len(task['log']))):
                print task['log'][j]['text'].replace('\n','')
            # print f,i, len(task['log'][i]['metadata']), len(task['log'][i+1]['metadata'])
            print f
            keep = raw_input()
            if keep == '0':
                del task['log'][i+1]
            else:
                del task['log'][i]
            changed = True
        i+=1

    if changed:
        fout = file('tempTasks/'+f,'w')
        fout.write(json.dumps(task,sort_keys=True,indent=4, separators=(',', ': ')))
        fout.close()

