#!/usr/bin/python
import os
import sys

__CGROUPFS__ = "/sys/fs/cgroup/cpu/"

def create (monitor, appname):
	path = __CGROUPFS__ + monitor + "/" + appname
	os.makedirs(path)


def remove (monitor, appname):
	path = __CGROUPFS__ + monitor + "/" + appname
	os.rmdir(path)	

def add (monitor, appname, pid):
	path = __CGROUPFS__ + monitor + "/" + appname + "/tasks"
	tasks = open(path, "a")
	pid = str(pid) + '\n'
	tasks.write(pid)
	tasks.flush()
	tasks.close()

def set_limit (monitor, appname, cpu_shares):
	path = __CGROUPFS__ + monitor + "/" + appname + "/cpu.shares"
	shares = open(path, "a")
	cpu_shares = str(cpu_shares) + '\n'
	shares.write(cpu_shares)
	shares.flush()
	shares.close()

if __name__ == "__main__":
	input_ = sys.stdin.readlines()
	for line in input_:
		tokens = line.strip().split(":")
		action, monitor, appname = tokens[0], tokens[1], tokens[3]
		if action == "create":
			create (monitor, appname)
		elif action == "remove":
			remove (monitor, appname)
		elif action == "add":
			pid = int(tokens[4])
			add (monitor, appname, pid)
		elif action == "set_limit":
			cpu_shares = int(tokens[5])
			set_limit (monitor, appname, cpu_shares)
		else:
			print ("Unknown command")
