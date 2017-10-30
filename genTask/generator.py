######################################################################
######################################################################
#  Copyright Tsung-Hsien Wen, Cambridge Dialogue Systems Group, 2017 #
######################################################################
######################################################################
import operator
import sys
import os
import json
import random


def slotRealisationFactory(s,domain):
    if s=='pricerange': return 'price range' 
    elif s=='phone': return 'phone number'
    elif s=='internet': return 'whether they have internet'
    elif s=='parking': return 'whether they have free parking'
    elif s=='departure': return 'departure site'
    elif s=='leaveAt': return 'departure time'
    elif s=='arriveBy': return 'arrival time'
    elif s=='stars': return 'star of the hotel'
    elif s=='type' and domain=='hotel': return 'hotel type'
    elif s=='type' and domain=='attraction': return 'attraction type'
    elif s=='food': return 'food type'
    elif s=='trainID': return 'train ID'
    elif s=='duration': return 'travel time'
    else: return s

def svRealisationFactory(sv,domain):
    s,v = sv
    if s=='food': return 'should serve <span class=\'emphasis\'>%s</span> food'% v
    if s=='pricerange': return 'should be in the <span class=\'emphasis\'>%s</span> price range'%v
    if s=='area': return 'should be in the <span class=\'emphasis\'>%s</span>'%v
    if s=='type': return 'should be in the type of <span class=\'emphasis\'>%s</span>'%v
    if s=='stars': return 'should have <span class=\'emphasis\'>a star of %s</span>'% v
    if s=='internet': 
        if v=='yes':  return 'should <span class=\'emphasis\'>include free wifi</span>'
        if v=='no': return '<span class=\'emphasis\'>doesn\'t need to include internet</span>'
    if s=='parking': 
        if v=='yes':  return 'should <span class=\'emphasis\'>include free parking</span>'
        if v=='no': return '<span class=\'emphasis\'>doesn\'t need to have free parking</span>'
    if s=='departure': return 'should depart from <span class=\'emphasis\'>%s</span>'%v
    if s=='destination': return 'should go to <span class=\'emphasis\'>%s</span>'%v
    if s=='arriveBy': return 'should <span class=\'emphasis\'>arrive by %s</span>'%v
    if s=='leaveAt': return 'should <span class=\'emphasis\'>leave after %s</span>'%v
    if s=='day': return 'should leave on <span class=\'emphasis\'>%s</span>'%v
    if s=='department': return 'should have the <span class=\'emphasis\'>%s</span> department'%v

def svRealisationFactoryCopy(sv,domain,prevDomain):
    s,v = sv
    if s=='pricerange': return 'should be in the <span class=\'emphasis\'>same price range as the %s</span>'%prevDomain
    if s=='area': return 'should be <span class=\'emphasis\'>in the same area as the %s</span>'% prevDomain
    if s=='destination': return 'should go to <span class=\'emphasis\'>%s</span>'%v
    if s=='arriveBy': return 'should <span class=\'emphasis\'>arrive by %s</span>'%v
    if s=='leaveAt': return 'should leave after <span class=\'emphasis\'>%s</span>'%v
    if s=='day': return 'should be on <span class=\'emphasis\'>the same day as the %s booking</span>'%prevDomain

def svRealisationFactoryAlternative(sv,domain):
    s,v = sv
    if s=='food': return 'serves <span class=\'emphasis\'>%s</span> food'%v
    if s=='pricerange': return 'is in the <span class=\'emphasis\'>%s</span> price range' %v 
    if s=='area': return 'is in the <span class=\'emphasis\'>%s</span>'%v
    if s=='type': return 'is in <span class=\'emphasis\'>the type of %s</span>'%v
    if s=='stars': return 'has <span class=\'emphasis\'>a star of %s</span>'%v
    if s=='internet': 
        if v=='yes':  return 'has <span class=\'emphasis\'>free wifi</span>'
        if v=='no': return '<span class=\'emphasis\'>doesn\'t have free wifi</span>'
    if s=='parking': 
        if v=='yes':  return 'has <span class=\'emphasis\'>free parking</span>'
        if v=='no': return '<span class=\'emphasis\'>doesn\'t have free parking</span>'
    if s=='departure': return 'departs from <span class=\'emphasis\'>%s</span>'%v
    if s=='destination': return 'goes to <span class=\'emphasis\'>%s</span>'%v
    if s=='arriveBy': return '<span class=\'emphasis\'>arrives by %s</span>'%v
    if s=='leaveAt': return '<span class=\'emphasis\'>leaves after %s</span>'%v
    if s=='day': return 'leaves on <span class=\'emphasis\'>%s</span>'%v
    if s=='department': return 'has the <span class=\'emphasis\'>%s department</span>'%v


def inform_generator(slots,domain,prevInfo):
    # preprocess slots
    slots = slots.items()
    random.shuffle(slots)
    # generate msg
    msgs = []
    index = 0
    while True:
        # generate informable slot infomation
        msg = ''
        if index<len(slots):
            # 1st message
            if  (slots[index][0] in prevInfo['info'] and slots[index][1]==prevInfo['info'][slots[index][0]]) or\
                (slots[index][0] in prevInfo['book'] and slots[index][1]==prevInfo['book'][slots[index][0]]):
                msg += 'The %s %s' % (domain,svRealisationFactoryCopy(slots[index],
                                        domain,prevInfo['domain']))
            else:
                msg += 'The %s %s' % (domain,svRealisationFactory(slots[index],domain))
            index +=1
            if index>=len(slots):
                msgs.append(msg)
                break
            # 2nd message
            if  (slots[index][0] in prevInfo['info'] and slots[index][1]==prevInfo['info'][slots[index][0]]) or\
                (slots[index][0] in prevInfo['book'] and slots[index][1]==prevInfo['book'][slots[index][0]]):
                msg += ' and %s' % (svRealisationFactoryCopy(slots[index],
                                        domain,prevInfo['domain']))
            else:
                msg += ' and %s' % svRealisationFactory(slots[index],domain)
            index += 1
            msgs.append(msg)
            if index>=len(slots):
                break
    return msgs

def inform_alter_generator(slots,domain):
    slots = slots.items()
    random.shuffle(slots)
    svs = [svRealisationFactoryAlternative(s2v,domain) for s2v in slots]
    tok = ', '
    if len(svs)>1:
        svs[-1] = 'and '+svs[-1]
    if len(svs)==2: tok = ' ' 
    return ['If there is no such %s, how about one that %s'%(domain,tok.join(svs))]

def inform_name_generator(slots,domain):
    return 'Its name is called <span class=\'emphasis\'>%s</span>' % slots['name']

def request_generator(slots,domain):
    random.shuffle(slots)
    slots = ['<span class=\'emphasis\'>'+slotRealisationFactory(s,domain)+'</span>' for s in slots]
    tok = ', '
    if len(slots)>1:
        slots[-1] = 'and '+slots[-1]
    if len(slots)==2: tok = ' '
    return 'Make sure you get ' + tok.join(slots)


def svRealisationFactoryBook(slot,value,prevInfo):
    if  (slot in prevInfo['book'] and prevInfo['book'][slot]==value) or\
        (slot in prevInfo['info'] and prevInfo['info'][slot]==value):
        # match in slot-value in previous domain
        if slot=='people': return 'the same group of people'
        if slot=='day': return 'the same day'
    else:
        if slot=='people': return value+' people'
        else: return value
        
week = ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']

def book_generator(slots,domain,prevInfo):
    if domain=='restaurant':
        msgs = ['Once you find the <span class=\'emphasis\'>%s</span> you want to book a table for <span class=\'emphasis\'>%s</span> at <span class=\'emphasis\'>%s</span> on <span class=\'emphasis\'>%s</span>'%(
                    domain,
                    svRealisationFactoryBook('people',slots['people'],prevInfo),
                    svRealisationFactoryBook('time',slots['time'],prevInfo),
                    svRealisationFactoryBook('day',slots['day'],prevInfo)),
                'Make sure you get the <span class=\'emphasis\'>reference number</span>']
        
        old_sv = {}
        if slots['invalid']==True:
            s = random.choice(['time','day'])
            old_sv[s] = slots[s]
            if s=='day': 
                wcpy = deepcopy(week)
                wcpy.remove(slots[s])
                v=random.choice(wcpy)
            if s=='time':v=str(int(slots['time'].split(':')[0])-1)+':'+slots['time'].split(':')[1]
            msgs = msgs[:1]+['If the booking fails how about <span class=\'emphasis\'>%s</span>'%v]+msgs[1:]
            slots[s] = v
        return msgs, old_sv

    elif domain=='hotel':
        msgs = ['Once you find the <span class=\'emphasis\'>%s</span> you want to book it for <span class=\'emphasis\'>%s</span> and <span class=\'emphasis\'>%s nights</span> starting from <span class=\'emphasis\'>%s</span>'%(
                    domain,
                    svRealisationFactoryBook('people',slots['people'],prevInfo),
                    svRealisationFactoryBook('stay',slots['stay'],prevInfo),
                    svRealisationFactoryBook('day',slots['day'],prevInfo)),
                'Make sure you get the <span class=\'emphasis\'>reference number</span>']
        
        old_sv = {}
        if slots['invalid']==True:
            s = random.choice(['stay','day'])
            old_sv[s] = slots[s]
            if s=='stay':   v=random.choice([str(x) for x in range(1,int(slots['stay']))])
            if s=='day':    
                wcpy = deepcopy(week)
                wcpy.remove(slots[s])
                v=random.choice(wcpy)
            slots[s] = v
            if s=='stay': v+=' nights'
            msgs = msgs[:1]+['If the booking fails how about <span class=\'emphasis\'>%s</span>'%v]+msgs[1:]
        return msgs, old_sv

    elif domain=='train':
        return ['Once you find the %s you want to make a booking for <span class=\'emphasis\'>%s</span>'%(domain,
                    svRealisationFactoryBook('people',slots['people'],prevInfo)),
                'Make sure you get the <span class=\'emphasis\'>reference number</span>'], {}
    elif domain=='hospital':
        return ['You want to check the <span class=\'emphasis\'>availability of the department</span>. Make sure you get the <span class=\'emphasis\'>scheduled time</span> and <span class=\'emphasis\'>reference number</span>']
    return '', {}





