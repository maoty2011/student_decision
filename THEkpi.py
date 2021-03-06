#Generate THE kpi for a group of people.
#THE kpi = weighted sum of individual kpis
#If target or control group too small, returns 0
#If an individual kpi gives division by zero, that part is zero-weighted

from __future__ import division
import numpy as np
import json
from datetime import datetime, timedelta


from population import Population



def THEKPI(population,segment):
    
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
    
    if len(TargetPeople)<5 or num_control<5:
        return "Too Small Sample"    
    
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
    
    offer_ids=[0 for i in range(0,len(offers))]
    
    for i in range(0,len(offers)):
            offer_ids[i]=offers[i].id
        
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
        
    KPI1=[]
    

    for i in range(0,len(offers)):
            try:
                KPI1.append(((spent_targ[i]- population.portfolio.values()[i].reward * num_rew[i])/len(offer_groups[i]))/(spent_cont[i]/num_control))
            except ZeroDivisionError:
                KPI1.append(0)
          
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
        
            
    KPI3=[]
    num_trx_targ=[0 for i in range(0,len(offers))]
    num_trx_cont=[0 for i in range(0,len(offers))]
    
    for i in range(0,len(offers)):
            try:
                KPI3.append(num_comp_targ[i]/num_view_targ[i])
            except ZeroDivisionError:
                KPI3.append(0)
#            if population.portfolio.values()[i].offer_type.weights[j] ==1 and population.portfolio.values()[i].offer_type.names[j]=='informational':
#                KPI3.append(0)
          
    for line in transcript:
        if line['event']=='transaction':
            for j in range(0,len(offer_groups)):
                if line['time']>=start_date[j] and line['time']<start_date[j]+72:
                    if line['person'] in offer_groups[j]:
                        num_trx_targ[j]+=1
                    if line['person'] not in TargetPeople:
                        num_trx_cont[j]+=1
    
    KPI4=[]
   
    for i in range(0,len(offers)):
        
        try:
            KPI4.append((num_trx_targ[i]/len(offer_groups[i]))/(num_trx_cont[i]/num_control))
        except ZeroDivisionError:
            KPI4.append(0)
     
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
    end_time=[offers[i].valid_until for i in range(0,len(offers))]
    max_timeB=0
    for line in transcript:
        if line['time']>max_timeB:
            max_timeB=line['time']
    max_timeA=max(end_time)
    max_time=max(max_timeA,max_timeB)
    
    DollarTrxB=[0 for i in range(0,len(offers))]
    DollarTrxA=[0 for i in range(0,len(offers))]
    
    for j in range(0,len(offers)):    
        for i in range(0,len(TrxBA)):
            if TrxBA[i][0] in offer_groups[j]:
                increaseB=(TrxBA[i][2]/TrxBA[i][3])/(i+1)
                DollarTrxB[j]=DollarTrxB[j]*i/(i+1)+increaseB
                increaseA=(TrxBA[i][4]/TrxBA[i][5])/(i+1)
                DollarTrxA[j]=DollarTrxA[j]*i/(i+1)+increaseA
    
    KPI5=[]
    
    for i in range(0,len(offers)):
        
        try:
            KPI5.append(DollarTrxA[i]/DollarTrxB[i])
        except ZeroDivisionError:
            KPI5.append(0)
  
            
    TrxHourB=[0 for i in range(0,len(offers))]
    TrxHourA=[0 for i in range(0,len(offers))]
      
    for j in range(0,len(offers)):
        for i in range(0,len(TrxBA)):
            if TrxBA[i][0] in offer_groups[j]:
                TrxHourB[j]=TrxHourB[j]*i/(i+1)+TrxBA[i][2]/(TrxBA[i][1])
                TrxHourA[j]=TrxHourA[j]*i/(i+1)+TrxBA[i][3]/(max_time-TrxBA[i][1])
                
    KPI6=[]
    
    for i in range(0,len(offers)):
        try:
            KPI6.append(TrxHourB[i]/TrxHourA[i])
        except ZeroDivisionError:
            KPI6.append(0)
            
       
    THEKPI=[0 for i in range(0,len(offers))]
    
    for i in range(0,len(offers)):
        THEKPI[i]=0.32*KPI1[i]+0.16*KPI3[i]+0.32*KPI4[i]+0.1*KPI5[i]+0.1*KPI6[i]
    
    return THEKPI


        
        
    


















