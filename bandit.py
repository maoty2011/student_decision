from numpy import *
from numpy.linalg import inv
import numpy as np
from scipy.stats import norm
import matplotlib.pyplot as plt
import json
from datetime import datetime, timedelta

from population import Population
from externalities import World, Offer, Transaction, Event, Categorical
import KPIs_segmented

class ContextualBandit(object):
	def __init__(self, population=None, cluster_file_name='cdata/population_clustered.json', time_stamp=0, num_arms=2, context_dim=2, prior=(1.0,1.0), delta=0.05, initialize=False):
		self.num_arms = num_arms
		self.context_dim = context_dim
		self.offer_list = []
		self.time_stamp = time_stamp
		if (population != None):
			self.offer_list = population.portfolio#.keys()
			self.num_arms = len(self.offer_list)
		
		self.prior = prior # use Gaussian

		self.alpha = 1 + np.sqrt(np.log(2/delta)/2)
		
		with open(cluster_file_name, 'r') as cluster_file:
			for line_number, line in enumerate(cluster_file):
			  text = line.strip()
			  self.cluster_dict = json.loads(text)
		
		clist = []
		for val in self.cluster_dict.values():
			clist += val
		self.context_dim =len(set(clist))
		
		self.population_dict = dict([(person_id, {'group': 'control',
                                                  'offer id': -1,
                                                  'viewed': 0,
                                                  'trx': 0,
                                                  'last offer time': 0,
                                                  'spend': 0.00}) for person_id in population.people])

		loc_dm = [np.identity(self.context_dim) for i in range(self.num_arms)] # list of "design matrix", actually A_a, but still call them design matrix
		self.design_matrix =[x[:] for x in loc_dm]  
		loc_rv = [np.zeros(shape=(self.context_dim,)) for i in range(self.num_arms)] # list of resp vectors, stored as column vectors, b_a
		self.respond_vector = [x[:] for x in loc_rv]
		self.control_vector = [1 for i in range(self.context_dim)]
	
	def control_grp_var(self,person_id):
		# variance of certain control group feature, given by the sample sizes
		
		return variance
		
	def add_result_seg(self, population, group):
		# adding result from a group of people, who belong to the same segmentation
		# group is a list of Person types
		andy = group[0] #pick a random user to calculate the context
		grp_num = self.cluster_dict[andy][0]
		
		# count group size among this segmentation. size_of_target[x] should return # of ppl in current group received offer x
		size_of_target = [0 for i in range(self.num_arms)]
		size_of_control = 0
		for person_id in group:
			#print(self.population_dict)
			tmp_offer_id = self.population_dict[person_id]['offer id']
			#print(tmp_group_id)
			if (tmp_offer_id >= 0):
				size_of_target[tmp_offer_id] += 1
			else:
				size_of_control +=1
		
		raw_feedback = KPIs_segmented.KPI1(population, group)
		print('group',self.cluster_dict[andy],raw_feedback)
		self.control_vector[grp_num] += (size_of_control)
		for trial_id in range(self.num_arms):
			loc_context = self.context(andy, trial_id, time_stamp=-1)
			# now update the design matrix and respond vector with a group of people given offer(trial_id)
			# the size of the group still counts. i.e. a test in a group of 500 ppl is more convincing than that in a group of 5 ppl.
			loc_size = size_of_target[trial_id]
			#self.design_matrix[trial_id] += loc_size*np.matmul(loc_context.reshape(self.context_dim,1),loc_context.reshape(1,self.context_dim))
			# update the respond vector with KPI
			
			if (type(raw_feedback)==str):
				1 # do something
				if (raw_feedback == "Control group is empty"):
					1 # no control, dont study?
				else:
					1 # no target, nothing to study
			else:
				feedback = raw_feedback[trial_id][1] # still could be NaN
				if (feedback != 'NaN'):
					# now study from exp
					self.design_matrix[trial_id] += loc_size*np.matmul(loc_context.reshape(self.context_dim,1),loc_context.reshape(1,self.context_dim))
					self.respond_vector[trial_id] += (loc_size*feedback)*loc_context
			#print((loc_size),loc_context,feedback)
		return raw_feedback
			
	def update_dict_from_population(self,population):
		# read the state of each customer from population and transcript file
		stats = dict([(person_id, {'group': 'control',
			                     'offer id': -1,
                           'viewed': 0,
                           'trx': 0,
                           'last offer time': 0,
                           'spend': 0.00}) for person_id in population.people])
    
		#print(type(stats),len(stats),stats)
		transcript_file_name=population.transcript_file_name
		time_stamp = -1
		with open(transcript_file_name, 'r') as transcript_file:
			for line_number, line in enumerate(transcript_file):
				text = line.strip()
				if text != '':
					record = json.loads(text)
	    
				current_person = record['person']
				if current_person in population.people:
					if record['event'] == 'offer received':
						stats[current_person]['group'] = 'target'
						current_offer_id = record['value']['offer id']
						if current_offer_id not in self.offer_list:
							self.offer_list.append(current_offer_id)
						stats[current_person]['offer id'] = self.offer_list.keys().index( record['value']['offer id'] )
		    
					if record['event'] == 'offer viewed':
						stats[current_person]['viewed'] += 1
   
					if record['event'] == 'transaction':
						stats[current_person]['trx'] += 1
						stats[current_person]['spend'] += record['value']['amount']
       
				#print(time_stamp, record['time'])
				time_stamp = max(time_stamp, record['time'])
   
		self.population_dict = stats

			
	def add_results_all_seg(self, population):
		for i in range(self.context_dim):
			loc_group = []
			for person_id in self.cluster_dict:
				if (self.cluster_dict[person_id] == [i]):
					loc_group.append(person_id)
			#print(i,"--->",len(loc_group))
			self.add_result_seg(population,loc_group) 	
	
	def context(self,current_user, trial_id, time_stamp):#maybe with current population too
		#return x(a,t)
		ans = np.ones(shape=(self.context_dim,)) #context-free
		if (current_user != None):
			if current_user in self.cluster_dict.keys():
				cur = self.cluster_dict[current_user][0]
				ans = np.array([int(i==cur) for i in range(self.context_dim)])
		return ans
		
	def add_result(self, trial_id, current_user, feedback, time_stamp): #add only one result to current bandit object
		#context=x(a,t) as column vector, feedback=r(t) as scalar
		loc_context = self.context(current_user, trial_id, time_stamp)
		self.design_matrix[trial_id] += np.matmul(loc_context.reshape(self.context_dim,1),loc_context.reshape(1,self.context_dim))
		self.respond_vector[trial_id] += feedback*loc_context
		self.time_stamp = max(time_stamp,self.time_stamp)
		
	def KPI1(self,population_stats_dict,group):
		# calculate KPI for a certain group, return an array of KPI regarding each offer
		TargetPeople=[]
		 
		return 0
		
	def add_results_from_group(self, population, group=None):
		# add results from a specified group (list of person_id, or None) with given population
		if (group==None):
			group = population.people
		#else:
			#work with specific group
		transcript_file_name=population.transcript_file_name
		print('add results from group read:',transcript_file_name)
		stats = dict([(person_id, {'group': 'control',
			                     'offer id': -1,
                           'viewed': 0,
                           'trx': 0,
                           'spend': 0.00}) for person_id in population.people])
    
		#print(type(stats),len(stats),stats)
		time_stamp = -1
		with open(transcript_file_name, 'r') as transcript_file:
			for line_number, line in enumerate(transcript_file):
				text = line.strip()
				if text != '':
					record = json.loads(text)
		    
				current_person = record['person']
				if current_person in group:
					if record['event'] == 'offer received':
						stats[current_person]['group'] = 'target'
						current_offer_id = record['value']['offer id']
						if current_offer_id not in self.offer_list:
							self.offer_list.append(current_offer_id)
						stats[current_person]['offer id'] = self.offer_list.keys().index( record['value']['offer id'] )
			    
					if record['event'] == 'offer viewed':
						stats[current_person]['viewed'] += 1
    
					if record['event'] == 'transaction':
						stats[current_person]['trx'] += 1
						stats[current_person]['spend'] += record['value']['amount']
        
				#print(time_stamp, record['time'])
				time_stamp = max(time_stamp, record['time'])
    
		self.population_dict = stats
		# collect some control group data here, this may be moved to kpi finally
		total_control_trx = 0.0
		total_control_num = 0.0
		for person_id in population.people:
			val = stats[person_id]
			if (val['group'] == 'control'):
				total_control_trx +=val['trx']
				total_control_num += 1
		print(total_control_trx, total_control_num)
		avg_control_trx = total_control_trx / total_control_num
		
		#counter = 0
		#cnt = [0 for i in range(self.num_arms)]
		#cnttrx = [0 for i in range(self.num_arms)]
		for person_id in group:
			val = stats[person_id]
			if (val['group'] == 'target'):
				feedback = int(val['trx']>0)# / avg_control_trx 
                # can change this feedback function
				#feedback = self.KPI(stats,person_id)
				
				#counter +=1
				#cnt[val['offer id']] +=1
				#cnttrx[val['offer id']] += feedback
				#print(counter,val['offer id'],person_id,feedback,time_stamp)
				
				self.add_result(val['offer id'],person_id,feedback,time_stamp)
				#print(self.design_matrix, self.respond_vector)
		#print(cnt)
		#print(cnttrx) 
	
	def send_recommendation(self, current_user=None, method='Gaussian'):#method='disjointUCB','Gaussian'
		#methods can be Bayesian, disjointUCB, hybirdUCB
		grp_num = self.cluster_dict[current_user][0]
		sampled_p = []
		for trial_id in range(self.num_arms):
			context = self.context(current_user, trial_id, self.time_stamp).reshape(self.context_dim,1)
			#print(context)
			theta = np.matmul(inv(self.design_matrix[trial_id]),self.respond_vector[trial_id])
			loc_mean = np.matmul(theta.transpose(),context) 
			loc_var1 = (np.matmul(np.matmul(context.reshape(1,self.context_dim),inv(self.design_matrix[trial_id])),context))
			loc_var2 = 1.0/self.control_vector[grp_num]
			
			loc_sd = np.sqrt(loc_var1+loc_var2)
			dist = norm(loc_mean, loc_sd)
			sampled_p += [dist.rvs()]
		#print(sampled_p)
		recommended_arm = sampled_p.index( max(sampled_p) )
		return self.offer_list.values()[recommended_arm]
	
	def get_dist_para(self, group_num=0, method='Gaussian'):#method='disjointUCB','Gaussian'
		#methods can be Bayesian, disjointUCB, hybirdUCB
		sampled_p = []
		for trial_id in range(self.num_arms):
			context = np.array([int(i==group_num) for i in range(self.context_dim)])
			#print(context)
			theta = np.matmul(inv(self.design_matrix[trial_id]),self.respond_vector[trial_id])
			loc_mean = np.matmul(theta.transpose(),context) 
			loc_sd = np.sqrt(np.matmul(np.matmul(context.reshape(1,self.context_dim),inv(self.design_matrix[trial_id])),context))
			
			dist = norm(loc_mean, loc_sd)
			sampled_p += [(loc_mean, loc_sd)]
		#print(sampled_p)
		return sampled_p
			
	def recommendation_to_csv(self,deliveries_file_name=None,delimiter='|',control_fraction=0.1):
		# write recommendations to a .csv file, in the same format as the delivery files
		# keep control_fraction amount of people as control group
		deliveries = []
		loc_offer_list = [self.offer_list.values()[i].id for i in range(self.num_arms)]
		counter = [[0 for j in range(self.num_arms+1)] for i in range(self.context_dim)]
		for i in range(self.context_dim):
        #separate group i first
			for users in self.cluster_dict.keys():
				if (self.cluster_dict[users]==[i]):
					val = self.population_dict[users]
					if np.random.random() < 1.0 - control_fraction:
					#only give offer to current target group people at a rate
						current_rec = self.send_recommendation(users).id
						deliveries.append((users, current_rec))
						counter[i][loc_offer_list.index(current_rec)] += 1
					else:
						counter[i][self.num_arms] += 1 #control group in group i people
                        
#		deliveries = []
#		for users in self.cluster_dict.keys():
#			val = self.population_dict[users]
#			if (val['group'] == 'target'):
#			#only give offer to people at a rate
#				if (numpy.random.random() <= 1-control_fraction):
#					current_rec = self.send_recommendation(users).id
#					deliveries.append((users, current_rec))
		
		print("deliver length",len(deliveries))
		if deliveries_file_name == None:
			return deliveries    
            
		with open(deliveries_file_name, 'w') as deliveries_file:
			for delivery in deliveries:
				print >> deliveries_file, delimiter.join(map(str, delivery))
		
		return counter #counter[i][j] = group i offer j people
	