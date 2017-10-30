######################################################################
######################################################################
#  Copyright Tsung-Hsien Wen, Cambridge Dialogue Systems Group, 2017 #
######################################################################
######################################################################

import json
import sys
import os
import re
import operator


fin = file(sys.argv[1])
db = json.load(fin)
fin.close()


for i in range(len(db)):
    entity = db[i]

    for s in ['entrance fee','price']:
        if s in entity:
            v = entity[s]
            if re.match('[0123456789\.]+',v):
                db[i][s] = v+' pounds' if v!='1' else v+' pound'
    s = 'duration'
    if s in entity:
        v = entity[s]
        db[i][s] = str(v)+' minutes' if v!=1 else str(v)+' minute'
       
print json.dumps(db, sort_keys=True,indent=4, separators=(',', ': '))


