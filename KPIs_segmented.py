#Generate KPIs 1-6 as lists (each entry = an offer)
#Takes segment as an input - should be a list of person ids.

from __future__ import division
import numpy as np
import json
from datetime import datetime, timedelta


from population import Population

#Generate KPI1 for each offer, for the first 3 days of the validity period
#KPI1: a person in target group spends x more than a person in control group
def KPI1(population,segment):
    transcript_file_name = population.transcript_file_name
    
    transcript=[]
    
    with open(transcript_file_name,'r') as transcript_file:
        for line_number, line in enumerate(transcript_file):
            text=line.strip()
            if text != '':
                record=json.loads(text)
                if record['person'] in segment:
                    transcript.append(record)
           
    TargetPeople=[]
    
    for line in transcript:
        if line['event']=='offer received':
            TargetPeople.append(line['person'])    
 
    num_control=len(segment)-len(TargetPeople)
    
    if len(TargetPeople)==0:
        return "Target group is empty"
    if num_control==0:
        return "Control group is empty"
   
    offers=population.portfolio.values()
    
    
    start_date=[0 for i in range(0,len(offers))]
    offer_ids=[0 for i in range(0,len(offers))]
    end_date=[0 for i in range(0,len(offers))]
    
    for i in range(0,len(offers)):
        start_date[i]=offers[i].valid_from
        
        
    for i in range(0,len(offers)):
        end_date[i]=offers[i].valid_until
        
    for i in range(0,len(offers)):
        offer_ids[i]=offers[i].id
    
    
    offer_groups=[[] for i in range(0,len(offers))]
    
    for line in transcript:
        if line['event']=='offer received':
            offer_groups[offer_ids.index(line['value']['offer id'])].append(line['person'])


    spent_targ = [0 for i in range(0, len(offers))]
    spent_cont = [0 for i in range(0, len(offers))]
    num_rew = [0 for i in range(0, len(offers))]
    
    for line in transcript:
        if line['event']=='transaction':
            for j in range(0,len(offer_groups)):
                if line['time']>=start_date[j] and line['time']<start_date[j]+72:
                    if line['person'] in offer_groups[j]:
                        spent_targ[j]=spent_targ[j]+line['value']['amount']
                    if line['person'] not in TargetPeople:
                        spent_cont[j]=spent_cont[j]+line['value']['amount']
      
    for line in transcript: 
        for j in range(0,len(offer_groups)):
            if line['time']>=start_date[j] and line['time']<start_date[j]+72:             
                if line['person'] in offer_groups[j] and line['event'] =='offer completed':
                    num_rew[j] +=1 
        
    KPI1=[[] for i in range(0,len(offers))]
    

    for i in range(0,len(offers)):
            try:
                KPI1[i].append(((spent_targ[i]- population.portfolio.values()[i].reward * num_rew[i])/len(offer_groups[i]))/(spent_cont[i]/num_control))
            except ZeroDivisionError:
                KPI1[i].append('NaN')
                print("group"," offer",i)
                print(((spent_targ[i]- population.portfolio.values()[i].reward * num_rew[i]),len(offer_groups[i])),(spent_cont[i],num_control))
            try:
                KPI1[i].append((spent_targ[i]- population.portfolio.values()[i].reward * num_rew[i])/len(offer_groups[i])-spent_cont[i]/num_control)
            except ZeroDivisionError:
                KPI1[i].append('NaN')
        
    return KPI1


#Generate KPI3 for each non-informational offer, for the first 3 days of the validity period
#KPI3: a fraction of completed offers after viewing them; only for target group 
# returns list of pairs: [fraction, difference]
def KPI3(population,segment):
    transcript_file_name = population.transcript_file_name
    
    transcript=[]
    
    with open(transcript_file_name,'r') as transcript_file:
        for line_number, line in enumerate(transcript_file):
            text=line.strip()
            if text != '':
                record=json.loads(text)
                if record['person'] in segment:
                    transcript.append(record)
              
    TargetPeople=[]
    
    for line in transcript:
        if line['event']=='offer received':
            TargetPeople.append(line['person'])    
 
    num_control=len(segment)-len(TargetPeople)
    
    if len(TargetPeople)==0:
        return "Target group is empty"
    if num_control==0:
        return "Control group is empty"
   
    offers=population.portfolio.values()
    
    
    start_date=[0 for i in range(0,len(offers))]
    offer_ids=[0 for i in range(0,len(offers))]
    end_date=[0 for i in range(0,len(offers))]
    
    for i in range(0,len(offers)):
        start_date[i]=offers[i].valid_from
        
        
    for i in range(0,len(offers)):
        end_date[i]=offers[i].valid_until
        
    for i in range(0,len(offers)):
        offer_ids[i]=offers[i].id
    
    
    offer_groups=[[] for i in range(0,len(offers))]
    
    for line in transcript:
        if line['event']=='offer received':
            offer_groups[offer_ids.index(line['value']['offer id'])].append(line['person'])


    num_view_targ = [0 for i in range(0, len(offers))]
    num_comp_targ = [0 for i in range(0, len(offers))]
    
    for line in transcript:
        if line['event']=='offer viewed':
            for j in range(0,len(offer_groups)):
                if line['time']>=min(start_date[k] for k in range(len(offers))) and line['time']<start_date[j]+72:
                    if line['person'] in offer_groups[j]:
                        num_view_targ[j] +=1
        if line['event']=='offer completed':
            for j in range(0,len(offer_groups)):
                if line['time']>=start_date[j] and line['time']<start_date[j]+72:
                    if line['person'] in offer_groups[j]:
                        num_comp_targ[j] +=1
        
            
    KPI3=[[] for i in range(0,len(offers))]
    
    frac = [0 for i in range(0, len(offers))]
    diff = [0 for i in range(0,len(offers))]
    
    for i in range(0,len(offers)):
            try:
                KPI3[i].append(num_comp_targ[i]/num_view_targ[i])
            except ZeroDivisionError:
                KPI3[i].append('NaN')
            if population.portfolio.values()[i].offer_type.weights[j] ==1 and population.portfolio.values()[i].offer_type.names[j]=='informational':
                    frac[i] = 'NA'
            KPI3[i].append(num_comp_targ[i]-num_view_targ[i])
    
    return KPI3



#Generate KPI4 for each offer, for the first 3 days of the validity period
#KPI4 = number of trx for people who received offer over number of trx for control group
#return list of pairs [fraction,difference]
def KPI4(population,segment,debugging=False):
    transcript_file_name = population.transcript_file_name
    if debugging:
    	print("KPI4 debug info")
    transcript=[]
    
    with open(transcript_file_name,'r') as transcript_file:
        for line_number, line in enumerate(transcript_file):
            text=line.strip()
            if text != '':
                record=json.loads(text)
                if record['person'] in segment:
                    transcript.append(record)
               
    TargetPeople=[]
    
    for line in transcript:
        if line['event']=='offer received':
            TargetPeople.append(line['person'])    
    
    num_control=len(segment)-len(TargetPeople)
    if debugging:
    	print(num_control,len(segment),len(TargetPeople))
              
    if len(TargetPeople)==0:
        return "Target group is empty"
    if num_control==0:
        return "Control group is empty"
    
    offers=population.portfolio.values()
    
    
    start_date=[0 for i in range(0,len(offers))]
    offer_ids=[0 for i in range(0,len(offers))]
    end_date=[0 for i in range(0,len(offers))]
    
    for i in range(0,len(offers)):
        start_date[i]=offers[i].valid_from
    
    if debugging:
    	print('start date',start_date)    
        
    for i in range(0,len(offers)):
        end_date[i]=offers[i].valid_until
        
    for i in range(0,len(offers)):
        offer_ids[i]=offers[i].id
    
    
    
    num_trx_targ=[0 for i in range(0,len(offers))]
    num_trx_cont=[0 for i in range(0,len(offers))]
    
    offer_groups=[[] for i in range(0,len(offers))]
    
    for line in transcript:
        if line['event']=='offer received':
            offer_groups[offer_ids.index(line['value']['offer id'])].append(line['person'])
            
    if debugging:
    	print(len(offer_groups))
    	print([len(g) for g in offer_groups])
    
    
    for line in transcript:
        if line['event']=='transaction':
            for j in range(0,len(offer_groups)):
                if line['time']>=start_date[j] and line['time']<start_date[j]+72:
                  if line['person'] in offer_groups[j]:
                     num_trx_targ[j]+=1
                  if line['person'] not in TargetPeople:
                     num_trx_cont[j]+=1
                else:
                	if debugging:
                		print(line['time'],start_date[j])
    
    if debugging:
    	print (num_trx_targ,num_trx_cont)
    KPI4=[[] for i in range(0,len(offers))]
   
    for i in range(0,len(offers)):
        
        try:
            KPI4[i].append((num_trx_targ[i]/len(offer_groups[i]))/(num_trx_cont[i]/num_control))
        except ZeroDivisionError:
            KPI4[i].append('NaN')
            if debugging:
            	print("group"," offer",i)
            	print((num_trx_targ[i],len(offer_groups[i])),(num_trx_cont[i],num_control))

        try:
            KPI4[i].append(num_trx_targ[i]/len(offer_groups[i]))#-num_trx_cont[i]/num_control
        except ZeroDivisionError:
            KPI4[i].append('NaN')
    
    # avg control trx and avg target trx at the end
    KPI4.append((num_trx_cont[0]/num_control))
    KPI4.append(sum(num_trx_targ)/len(TargetPeople))
    return KPI4


#Generate KPI5 for each offer
#KPI5 = $ per trx after viewing over $ per trx before viewing
#NB: only calculated for subset of target group - those who had trx before and after viewing offer
def KPI5(population,segment):

    
    transcript_file_name = population.transcript_file_name
    
    transcript=[]
    
    with open(transcript_file_name,'r') as transcript_file:
        for line_number, line in enumerate(transcript_file):
            text=line.strip()
            if text != '':
                record=json.loads(text)
                if record['person'] in segment:
                    transcript.append(record)
               
    TargetPeople=[]
    
    for line in transcript:
        if line['event']=='offer received':
            TargetPeople.append(line['person'])                  
    
    num_control=len(segment)-len(TargetPeople)
    

    if len(TargetPeople)==0:
        return "Target group is empty"
    if num_control==0:
        return "Control group is empty"

    
    offers=population.portfolio.values()
    
    offer_groups=[[] for i in range(0,len(offers))]
    
    offer_ids=[0 for i in range(0,len(offers))]
    
    for i in range(0,len(offers)):
            offer_ids[i]=offers[i].id
        
    for line in transcript:
        if line['event']=='offer received':
            offer_groups[offer_ids.index(line['value']['offer id'])].append(line['person'])
    
    Trx=[]
    
    for line in transcript:
        if line['event']=='offer viewed':
            Trx.append([line['person'],line['time'],0,0,0,0])
    
    for line in transcript:
        if line['event']=='transaction':
            for entry in Trx:
                if line['person']==entry[0]:
                    if line['time']<entry[1]:
                        entry[2]=entry[2]+line['value']['amount']
                        entry[3]+=1
                    elif line['time']>entry[1]:
                        entry[4]=entry[4]+line['value']['amount']
                        entry[5]+=1
                    break
                    
    for line in transcript:
        if line['event']=='offer completed':
            for entry in Trx:
                if line['person']==entry[0]:
                    if line['time']<entry[1]:
                        entry[2]=entry[2]-line['value']['reward']
                    if line['time']>entry[1]:
                        entry[4]=entry[4]-line['value']['reward']
                    break
    
    #keep only people who transacted both before and after their viewtime
    TrxBA=[]
    for line in Trx:
        if line[2]>0 and line[4]>0:
            TrxBA.append(line)
    
    
    DollarTrxB=[0 for i in range(0,len(offers))]
    DollarTrxA=[0 for i in range(0,len(offers))]
    
    for j in range(0,len(offers)):    
        for i in range(0,len(TrxBA)):
            if TrxBA[i][0] in offer_groups[j]:
                increaseB=(TrxBA[i][2]/TrxBA[i][3])/(i+1)
                DollarTrxB[j]=DollarTrxB[j]*i/(i+1)+increaseB
                increaseA=(TrxBA[i][4]/TrxBA[i][5])/(i+1)
                DollarTrxA[j]=DollarTrxA[j]*i/(i+1)+increaseA
    
    KPI5=[[] for i in range(0,len(offers))]
    
    for i in range(0,len(offers)):
        
        try:
            KPI5[i].append(DollarTrxA[i]/DollarTrxB[i])
        except ZeroDivisionError:
            KPI5[i].append('NaN')
        KPI5[i].append(DollarTrxA[i]-DollarTrxB[i])
    

    return KPI5


#Generate KPI6 for each offer
#KPI6 = #trx per time after viewing over #trx per time before viewing
#NB: only calculated for subset of target group - those who had trx before and after viewing offer
def KPI6(population,segment):

    
    transcript_file_name = population.transcript_file_name
    
    transcript=[]
    
    with open(transcript_file_name,'r') as transcript_file:
        for line_number, line in enumerate(transcript_file):
            text=line.strip()
            if text != '':
                record=json.loads(text)
                if record['person'] in segment:
                    transcript.append(record)
               
    TargetPeople=[]
    
    for line in transcript:
        if line['event']=='offer received':
            TargetPeople.append(line['person'])                  
    
    num_control=len(segment)-len(TargetPeople)
    
    if len(TargetPeople)==0:
        return "Target group is empty"
    if num_control==0:
        return "Control group is empty"    
    
    offers=population.portfolio.values()
    
    offer_groups=[[] for i in range(0,len(offers))]
    
    offer_ids=[0 for i in range(0,len(offers))]
    
    for i in range(0,len(offers)):
            offer_ids[i]=offers[i].id
        
    for line in transcript:
        if line['event']=='offer received':
            offer_groups[offer_ids.index(line['value']['offer id'])].append(line['person'])
    
    Trx=[]
    
    for line in transcript:
        if line['event']=='offer viewed':
            Trx.append([line['person'],line['time'],0,0])
    
    for line in transcript:
        if line['event']=='transaction':
            for entry in Trx:
                if line['person']==entry[0]:
                    if line['time']<entry[1]:
                        entry[2]+=1
                    elif line['time']>entry[1]:
                        entry[3]+=1
                    break
                    
    
    
    #keep only people who transacted both before and after their viewtime
    TrxBA=[]
    for line in Trx:
        if line[2]>0 and line[3]>0:
            TrxBA.append(line)
    # set end of time to be maximum of last viewtime and end of validity period
    end_time=[offers[i].valid_until for i in range(0,len(offers))]
    max_timeB=0
    for line in transcript:
        if line['time']>max_timeB:
            max_timeB=line['time']
    max_timeA=max(end_time)
    max_time=max(max_timeA,max_timeB)

    TrxHourB=[0 for i in range(0,len(offers))]
    TrxHourA=[0 for i in range(0,len(offers))]
      
    for j in range(0,len(offers)):
        for i in range(0,len(TrxBA)):
            if TrxBA[i][0] in offer_groups[j]:
                TrxHourB[j]=TrxHourB[j]*i/(i+1)+TrxBA[i][2]/(TrxBA[i][1])
                TrxHourA[j]=TrxHourA[j]*i/(i+1)+TrxBA[i][3]/(max_time-TrxBA[i][1])
                
    KPI6=[[] for i in range(0,len(offers))]
    
    for i in range(0,len(offers)):
        try:
            KPI6[i].append(TrxHourB[i]/TrxHourA[i])
        except ZeroDivisionError:
            KPI6[i].append('NaN')
        KPI6[i].append(TrxHourB[i]-TrxHourA[i])
        
        
    
    return KPI6

