"""Run an experiment with given population and portfolio, where offers are assigned based on contextual bandit"""

import logging
import unittest

import argparse
import os.path
import glob
import datetime
import numpy
import shutil
import copy
import json

from externalities import World, Offer, Transaction, Event, Categorical
from person import Person
from population import Population

import bandit
import segmentation
import KPIs_segmented

dt_fmt = '%Y%m%d'
now = datetime.datetime.strptime('20170718', dt_fmt)


def mkdir_if_missing(path):
    if not os.path.isdir(path):
        if os.path.exists(path):
            raise ValueError('ERROR - the path name {} is already in use by a file or link.'.format(path))
        else:
            os.makedirs(path)


def assign_offers(population, deliveries_file_name, deliveries_log_file_name, control_fraction=0.25, delimiter='|', clean_path=True):

    if clean_path:
        data_file_names = glob.glob(os.path.join(population.deliveries_path, '*'))
        for data_file_name in data_file_names:
            os.remove(data_file_name)

    offer_ids = population.portfolio.keys()
    deliveries = list()
    
    
    for person_id in population.people.keys():
        # hold out a fraction of people as control
        if numpy.random.random() < 1.0 - control_fraction:
            # make random deliveries to the rest
            deliveries.append((person_id, numpy.random.choice(offer_ids)))

    # write the deliveries file
    with open(deliveries_file_name, 'w') as deliveries_file:
        for delivery in deliveries:
            print >> deliveries_file, delimiter.join(map(str, delivery))

    # make a copy of the delivery file
    shutil.copy(deliveries_file_name, deliveries_log_file_name)


def main(args):
    # file paths, working directory = args.data_path = cluster_data ATM
    num_repeat = int(args.repeat) # use this to run several simulations at once
    
    # a problem now is that I didnt write a method to save bandit objects to a file
    # has to generate one at the beginning and keep it in the memory at all time, so it updates itself.
    # one way to save it under Gaussian hypothesis would be just saving the design matrices and respond vectors. todo
    
    f_table = open('table.txt', 'w')
    
    # run an inital round
    print("============= Initial Round Started =============")
    data_read_path = args.data_path
    data_write_path = args.data_path + str(0)
    print("current working directories: write",data_write_path,"read",data_read_path)
    
#    data_write_path = args.data_path + str(num_repeat)
#    data_read_path = args.data_path + str(num_repeat-1)
#    if (num_repeat == 0):
#        data_read_path = args.data_path
#    print(data_write_path,data_read_path)
    
    # to read
    delivery_log_path = os.path.join(data_read_path, 'delivery_log')
    deliveries_path = os.path.join(data_read_path, 'delivery')
    transcripts_file_read = os.path.join(data_read_path, 'transcript.json')
    population_file_read = os.path.join(data_read_path, 'population.json')
    cluster_file_read = os.path.join(data_read_path, 'population_clustered.json')
    deliveries_file_name = os.path.join(deliveries_path, 'test_deliveries.csv')
    deliveries_log_file_name = os.path.join(delivery_log_path, 'test_deliveries.csv')
    
    # to write
    transcripts_file_write = os.path.join(data_write_path, 'transcript.json')
    population_file_write = os.path.join(data_write_path, 'population.json')
    
    #read from population JSON file, 
    population_file_name = population_file_read
    population = Population.from_json(population_file_name)
    print("read transcript from:",population.transcript_file_name)
    
    # read finished, redirect the population so that it reads from and writes to the right folder
    population.deliveries_path = deliveries_path
    
    #build world
    world = population.world

    # create directories if they don't already exist
    mkdir_if_missing(data_write_path)
    mkdir_if_missing(delivery_log_path)
    mkdir_if_missing(deliveries_path)
    
    # run the cluster with historical data, then write it to cluster_file_read
    segmentation.segment_pop(population_file_read,transcript_file_name=transcripts_file_read,output_file_name=cluster_file_read)
    
    #maybe we can print some KPI values for current population
    #print("control number","target number")
    #print("current overall KPI:",KPIs_segmented.KPI1(population,population.people))
    
    # write population file. Doesn't seem to be changing ATM, but we may what to shrink group size for each step.
    population2 = copy.deepcopy(population)
    population2.transcript_file_name = transcripts_file_write
    with open(population_file_write, 'w') as population_file:
        print >> population_file, population2.to_json()
    
    # generate a segmentation file in read_path, named cluster_file_read
    #segmentation.segment_pop(population_file_read,transcript_file_name=transcripts_file_read,output_file_name=cluster_file_read)
    
    #here deliveries are generated by bandit, written to file
    #cluster_file_name='cluster_data/population_clustered.json'
    myBandit = bandit.ContextualBandit(population, cluster_file_name=cluster_file_read, initialize=True)
    myB2 = copy.deepcopy(myBandit)
    #myBandit.add_results_all_seg(population)
    
    #print(myBandit.design_matrix)
    
    table=myBandit.recommendation_to_csv(deliveries_file_name = deliveries_file_name)
    shutil.copy(deliveries_file_name, deliveries_log_file_name)
    print("Decision log saved to",deliveries_log_file_name)
    
    json.dump(table,f_table)
    f_table.write('\n')
    print(myBandit.design_matrix)
    #print(myBandit.respond_vector)
    #deliveries = recommendation_to_csv(population)

    #redirects the population transcript path, so that it writes to the correct folder
    population.transcript_file_name = transcripts_file_write
    print("simulation transcript will be written to",population.transcript_file_name)
    
    # update the offer valid periods as if they were new, then simulate
    #print population.portfolio.values()[0].to_serializable()
    print population.people.values()[0].to_serializable()
    # [(offer.valid_from, offer.valid_until,offer.id) for offer in population.portfolio.values()]
    for offer in population.portfolio.values():
        offer.valid_from += 3*4*6
        offer.valid_until += 3*4*6
    population.simulate(n_ticks=3*4)
    
    # write population file. Doesn't seem to be changing ATM, but we may what to shrink group size for each step.
    print("============= Initial Round Simulation done =============")
    
    """a = population.world.to_serializable()
    print('world ok',a)
    b = [person.to_serializable() for person in population.people.values()]
    print('person ok',b[0])
    c = [offer.to_serializable() for offer in population.portfolio.values()]
    print('offer ok',c[0],c[1])
    print(population.portfolio.values())
    print(population.deliveries_path)
    print(population.transcript_file_name)
""" 
    
    # now starts repeating the bandit algo
    n_round = 1
    while(n_round<=num_repeat):
        print("============= Round", n_round, "Started =============")
        data_write_path = args.data_path + str(n_round)
        data_read_path = args.data_path + str(n_round-1)
        print("current working directories: write",data_write_path,"read",data_read_path)
        
        # to read
        delivery_log_path = os.path.join(data_read_path, 'delivery_log')
        deliveries_path = os.path.join(data_read_path, 'delivery')
        transcripts_file_read = os.path.join(data_read_path, 'transcript.json')
        population_file_read = os.path.join(data_read_path, 'population.json')
        #cluster_file_read = os.path.join(data_read_path, 'population_clustered.json')
        deliveries_file_name = os.path.join(deliveries_path, 'test_deliveries.csv')
        deliveries_log_file_name = os.path.join(delivery_log_path, 'test_deliveries.csv')
    
        # to write
        transcripts_file_write = os.path.join(data_write_path, 'transcript.json')
        population_file_write = os.path.join(data_write_path, 'population.json')
    
        #read from population JSON file, 
        #population_file_name = population_file_read
        #population = Population.from_json(population_file_name)
        #print(population.transcript_file_name)
        
        print("read transcript from:",population.transcript_file_name)
        #pl = [(offer.valid_from, offer.valid_until,offer.id) for offer in population.portfolio.values()]
        #print(pl)
        if (n_round>0):
        	print("current overall KPI:",KPIs_segmented.KPI4(population,population.people,debugging=True))
    
        # read finished, redirect the population so that it reads from and writes to the right folder
        population.deliveries_path = deliveries_path
        
        # create directories if they don't already exist
        mkdir_if_missing(data_write_path)
        mkdir_if_missing(delivery_log_path)
        mkdir_if_missing(deliveries_path)
        
        #here deliveries are generated by bandit, written to file
        #cluster_file_name='cdata/population_clustered.json'
        myBandit.update_dict_from_population(population)
        myBandit.add_results_all_seg(population)
        
        for i in range(myBandit.context_dim):
        	print(myBandit.get_dist_para(group_num=i))
        
        #table = myBandit.recommendation_to_csv(deliveries_file_name = deliveries_file_name)
        table = myB2.recommendation_to_csv(deliveries_file_name = deliveries_file_name)
        shutil.copy(deliveries_file_name, deliveries_log_file_name)
        print("Decision log saved to",deliveries_log_file_name)
        
        json.dump(table,f_table)
        f_table.write('\n')
        print(myBandit.design_matrix)
        #print(myBandit.respond_vector)
        #deliveries = recommendation_to_csv(population)
    
        #redirects the population transcript path, so that it writes to the correct folder
        population.transcript_file_name = transcripts_file_write
        print("simulation transcript will be written to",population.transcript_file_name)
        
        #print population.portfolio.values()[0].to_serializable()
        #print population.people.values()[0].to_serializable()
        print population.people.values()[0].last_viewed_offer.to_serializable()
        
        #print("World Time:",population.world.world_time)
        #population.world.world_time = 0
        #print("Rewind Time:",population.world.world_time)
        for offer in population.portfolio.values():
            offer.valid_from += 3*4*6
            offer.valid_until += 3*4*6
        population.simulate(n_ticks=3*4)
    
        # write population file. Doesn't seem to be changing ATM, but we may what to shrink group size for each step.
        print("============= Round", n_round, "Simulation done =============")
        
        n_round +=1


    f_table.close()
    return 0


def get_args():
    """Build arg parser and get command line arguments

    :return: parsed args namespace
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--data-path", default="cdata", help="data path file name")
    parser.add_argument("--n-proc", default=1, help="number of Processes to use for simulation")
    parser.add_argument("--repeat", default=0, help="number of periods to repeat")

    args = parser.parse_args()

    return args


if __name__ == '__main__':
    main(get_args())

