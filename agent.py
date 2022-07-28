import random as rand # For randomization
import uuid # For generating unique trait IDs

class Agent:
	# Create a new agent.
	def __init__(self, params, group):
		self.group = group
		self.trait_types = []
		self.trait_levels = []
		self.current = None

	# Innovation
	def il(self, params):
		if rand.random() < params['P_INNOVATE']:
			# Does the agent have an empty repertoire?
			if len(self.trait_types) == 0:
				# Create a new trait of a new type
				self.trait_types.append(uuid.uuid4())
				self.trait_levels.append(1)
			else:
				# Create a new trait of complexity C + 1 of the same type as the agent's most complex trait
				trait = self.current
				if sum(self.trait_levels) >= round(self.trait_levels[trait] ** params['MU']):
					self.trait_levels[trait] += 1

	# Social learning
	def sl(self, params, partner):
		# Give up if the partner has nothing to learn
		if partner.current is None:
			return
		
		if rand.random() < params['P_COPY']:
			trait = partner.current
			type = partner.trait_types[trait]
			level = partner.trait_levels[trait]
			
			# Does the agent already have a trait of this type?
			if type in self.trait_types:
				# Create a new trait of complexity C + 1 of the same type as the copied trait
				trait = self.trait_types.index(type)
				if level > self.trait_levels[trait]:
					self.trait_levels[trait] += 1
			else:
				# Create a new trait of the same type
				self.trait_types.append(type)
				self.trait_levels.append(1)


	# Exhibit a behavior
	def exhibit(self):
		if len(self.trait_types) > 0:
			self.current =  Agent.argmax(self.trait_levels)

	# Find the maximum value of a list, selecting randomly if there's more than one
	def argmax(vals):
		val = max(vals)
		indices = [index for index in range(len(vals)) if vals[index] == val]
		return indices[rand.randint(0, len(indices) - 1)]