######################################################################
######################################################################
#  Copyright Tsung-Hsien Wen, Cambridge Dialogue Systems Group, 2017 #
######################################################################
######################################################################
import sys
import os
import operator
import json
import random

random.seed(0)

tasklist = sorted(os.listdir('tempTasks'))
fin = file('tmp/finishedList')
finished = [l.replace('\n','') for l in fin.readlines()][1:]
fin.close()


todos = []

for filename in tasklist:
    
    print filename
    fin = file('tempTasks/'+filename)
    task= json.load(fin)
    fin.close()
    if 'eod' in task['goal'] and task['goal']['eod'] and len(task['log'])!=0:
        # indicating it is finished
        if  (len(task['log'])<10 and 'MUL' in filename) or\
            (len(task['log'])<4  and 'SNG' in filename) or\
            len(task['log'])%2==1:
            # if length is too short, not finished
            todos.append(filename)
        elif filename in finished: 
            # if already in finished list
            pass
        else:
            # if cannot decide
            for i in range(len(task['log'])):
                print task['log'][i]['text']
            ans = raw_input('%s is finished? (y/n), %d ' % (filename,len(task['log']))) 
            print
            if ans=='n':
                # not finished
                todos.append(filename)
            if ans=='y':
                # finished
                finished.append(filename)
            
    else: 
        todos.append(filename)


fout = file('tmp/taskList','w')
fout.write('0\n')
fout.write('\n'.join(todos))
fout.close()

fout = file('tmp/finishedList','w')
fout.write('\n'.join(['0']+finished))
fout.close()


