######################################################################
######################################################################
#  Copyright Tsung-Hsien Wen, Cambridge Dialogue Systems Group, 2017 #
######################################################################
######################################################################
import os
import sys
import json
import operator


tasklist = sorted(os.listdir('tempTasks'))

for filename in tasklist:
    
    fin = file('tempTasks/'+filename)
    task= json.load(fin)
    fin.close

    if len(task['log'])!=0:
        print filename
    else:
        os.system('cp genTask/tasks/'+filename+' '+'tempTasks/'+filename)


