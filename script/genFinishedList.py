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
fin = file('lock/taskList')
todos = [l.replace('\n','') for l in fin.readlines()][1:]
fin.close()


finished = []

for filename in tasklist:
    
    fin = file('tempTasks/'+filename)
    task= json.load(fin)
    fin.close()
    
    if filename not in todos:
        finished.append(filename)


print '\n'.join(['0']+finished)
#fout = file('tmp/finishedList','w')
#fout.write('\n'.join(['0']+finished))
#fout.close()


