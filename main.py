# Ingroup-Biased Copying Promotes Cultural Diversity and Complexity (https://tinyurl.com/ingroupdiversity)
# Author: Marcel Montrey (marcel.montrey@mail.mcgill.ca)

from multiprocessing import Pool, cpu_count # For running parallel simulations
import os # For creating directories
import random as rand # For randomization
import sys # For getting command line arguments
import networkx as nx # For generating graphs
import copy # For making deep copies of the parameters dictionary
import math # For the floor function

import agent # Class instantiating simulated agents

# Set and iterate over simulation parameters
def main():
	params = {
		# Strings
		'PATH': 'data',
		'NETWORK_TYPE': 'COMPLETE', # COMPLETE or RELAXED_CAVEMAN
		
		# Integers
		'N_RUNS': 20, # Number of simulations per parameter value
		'N_STEPS': 10000, # Maximum number of time steps
		'N_AGENTS': 400, # Number of agents
		'N_GROUPS': 20, # Number of groups
		
		# Floats
		'P_REWIRE': 0.2, # Probability of a within-group connection being rewired
		'P_BIAS': frange(0, 0.9, 0.1), # Ingroup copying bias strength
		'P_INNOVATE': 0.01, # Probability of innovation
		'P_COPY': [.1, .2], # Probability of copying
		'MU': 1.5, # How strongly innovation depends on cultural diversity
		'P_REPLACE': 0.001, # Replacement rate
	}
	
	# Parameters to iterate over
	itr = [p for p in params if isinstance(params[p], list)]
	
	# If we're iterating over more than one parameter, iterate over the parameter with fewer settings first
	if len(itr) > 1 and len(params[itr[1]]) < len(params[itr[0]]):
		itr[0], itr[1] = itr[1], itr[0]
	
	# Not iterating over any parameter
	if len(itr) == 0:
		# Run simulations in parallel
		run_parallel(params)
		
	# Iterating over at least one parameter
	else:
		# Iterate over the first parameter
		for i in range(len(params[itr[0]])):
			# Set the first parameter
			current = copy.deepcopy(params)
			current[itr[0]] = params[itr[0]][i]
			
			# Print the current parameter
			print('[{0}={1}]'.format(itr[0], current[itr[0]]))
			
			# Iterating over only one parameter
			if len(itr) == 1:
				# Set the current path
				current['PATH'] = '{0}/{1}={2}'.format(params['PATH'], itr[0], current[itr[0]])
				
				# Run simulations in parallel
				run_parallel(current)
				
			# Iterating over two parameters
			elif len(itr) == 2:
				# Iterate over the second parameter
				for j in range(len(params[itr[1]])):
					# Set the second parameter
					current[itr[1]] = params[itr[1]][j]
					
					# Set the current path
					current['PATH'] = '{0}/{1}={2}/{3}={4}'.format(params['PATH'], itr[0], current[itr[0]], itr[1], current[itr[1]])
					
					# Print the current parameter
					print('  [{0}={1}]'.format(itr[1], current[itr[1]]))
					
					# Run simulations in parallel
					run_parallel(current)

# Run multiple simulations in parallel		
def run_parallel(params):
	# Set the number of threads to the cpu count (or override by passing the desired number of threads as a command line argument)
	pool = Pool(cpu_count() if len(sys.argv) == 1 else int(sys.argv[1]))
	pool.map(run, [params] * params['N_RUNS'])
	pool.close()

# Run a simulation
def run(params):
	# Create agents
	agents = []
	for i in range(params['N_AGENTS']):
		group = math.floor(i / params['N_AGENTS'] * params['N_GROUPS'])
		agents.append(agent.Agent(params, group))
	
	# Generate a complete graph
	if params['NETWORK_TYPE'] == 'COMPLETE':
		graph = nx.complete_graph(params['N_AGENTS'])
	# Generate a relaxed caveman graph
	elif params['NETWORK_TYPE'] == 'RELAXED_CAVEMAN':
		graph = None
		# Repeat until the graph does not contain any isolated agents
		while graph is None or nx.degree_histogram(graph)[0] > 0:
			graph = nx.generators.relaxed_caveman_graph(params['N_GROUPS'], round(params['N_AGENTS'] / params['N_GROUPS']), params['P_REWIRE'])
	
	# Each individual's list of neighbors and the subset belonging to the ingroup
	neighbors = []
	neighbors_ig = []
	for i in range(params['N_AGENTS']):
		neighbors.append(list(nx.neighbors(graph, i)))
		neighbors_ig.append([])
		for j in neighbors[i]:
			if agents[i].group == agents[j].group:
				neighbors_ig[i].append(j)
	
	# Initialize data tracking
	data = [[0 for j in range(2)] for i in range(params['N_STEPS'] + 1)] 
	data[0][0] = 'trait_types'
	data[0][1] = 'trait_complexity'

	# Time step
	for step in range(params['N_STEPS']):
		# Randomize interaction order
		order = list(range(len(agents)))
		rand.shuffle(order)
		
		# Innovation phase
		for i in order:
			agents[i].il(params)
		
		# Social learning phase
		for i in order:
			# Apply the ingroup copying bias
			if rand.random() < params['P_BIAS'] and len(neighbors_ig[i]) > 0:
				j = rand.randint(0, len(neighbors_ig[i]) - 1)
				partner = agents[neighbors_ig[i][j]]
			# Copy at random
			else:
				j = rand.randint(0, len(neighbors[i]) - 1)
				partner = agents[neighbors[i][j]]
			
			agents[i].sl(params, partner)
		
		# Exhibition phase
		for i in order:
			agents[i].exhibit()
		
		# Replacement phase
		for i in order:
			if rand.random() < params['P_REPLACE']:
				agents[i] = agent.Agent(params, agent.Agent(params, agents[i].group))
		
		# Record data
		data[step + 1][0] = sum([len(a.trait_types) for a in agents]) / params['N_AGENTS']
		data[step + 1][1] = sum([max(a.trait_levels, default=0) for a in agents]) / params['N_AGENTS']

	# Make sure the directory path exists
	if not os.path.isdir(params['PATH']):
		os.makedirs(params['PATH'])
	
	# Save data to a new directory
	path = create_dir(params)
	with open(path + '/results.csv', 'w') as file:
		for i in range(step):
			file.write(','.join(map(str, data[i])) + '\n')

# Create a list of evenly spaced parameter values
def frange(start, stop, step, digits=5):
	return([round(start + step * i, digits) for i in range(round((stop - start) / step) + 1)])

# Create a new numbered directory
def create_dir(params):
	dir = 0
	while os.path.isdir('{0}/{1}'.format(params['PATH'], dir)):
		dir += 1
	path = '{0}/{1}'.format(params['PATH'], dir)
	
	try:
		os.makedirs(path)
	except:
		path = create_dir(params)
	
	return(path)

# Make sure this is an independent process
if __name__ == '__main__':
	main()
