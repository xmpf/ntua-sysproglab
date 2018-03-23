#!/usr/bin/python
import sys
"""
Michalis Papadopoullos
el14702
"""

default_resources = 2000

class ResourceManager:
	def __init__(self, total):
		self.total = total
		self.available = total
		self.used = 0
		self.policies = []	

	def avail(self):
		return self.available
		
	def used(self):
		return self.used
	
	def assign(self, shares):
		self.available -= shares
		self.used += shares
	
	def new_policy(self, policy):
		self.policies.append(policy)
		
	def consistent(self, value):
		return (value <= self.total)
		
if __name__ == "__main__":
	input_ = sys.stdin.readlines()
	cpu = ResourceManager (default_resources)
	total_shares = 0
	for line in input_:
		tokens = line.strip().split(":")
		appname, cpu_shares = tokens[1], tokens[3]
		total_shares += int(cpu_shares)
		if int(cpu_shares) <= cpu.available:
		cpu.assign(int(cpu_shares))
		cpu.new_policy([appname, cpu_shares])
	
	score = 1.0 if cpu.consistent(total_shares) else -1.0
	sys.stdout.write("score:" + str(float(score)) + "\n")
	
	percentage = 0
	if total_shares != 0:
		percentage = float(cpu.total) / float(total_shares)
	
	for policy in cpu.policies:
		cpu_shares_assign = int(policy[1]) * percentage
		sys.stdout.write("set_limit:" + policy[0] + ":cpu.shares:" + str(int(cpu_shares_assign)) + "\n") 
