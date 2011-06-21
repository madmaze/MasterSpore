##############
# GF.py - GlobalFunctions
##############
import os
import sys
import time
import CLnode

#######################
# 0 = none
# 1 = info
# 2 = debug
logLevel=0
######################
nodes=[]
reqests=[]

# Simple wrapper for running Shell commands
def run(cmd):
	f=os.popen(cmd)
	buf=""
	for i in f.readlines():
		buf+=i
	return buf.strip()

# Logging function only prints out if its of the currently set logging level
def log(msg, lvl):
	if logLevel >= lvl:
		print msg

# converts v to bool if its a string
def str2bool(v):
	if type(v) is type(bool):
		return v
	else:
		return str(v).lower() in ("True", "true", "t", "1")

# Adds new nodes to GF.nodes or updates if existing
# This is specifically adjusted to only update the fields 
# that contain metadata that cannot be resolved from ec2-describe-instances  
def addNewNodes(new):
	#TODO: double check that it never wrongly updates the meta data
	# print "adding",len(new)
	for n in new:
		exists=instExists(n)
		if exists>=0:
			# Update metadata
			nodes[exists].instName=n.instName
			nodes[exists].deployed=n.deployed
			nodes[exists].master=n.master
			#print "already exists"
		else:
			if n.status == "terminated" or n.status == "shutting-down":
				print "will be dropped:",str(n)
			else:
				#print "appending"
				nodes.append(n.copy())

# Check whether an instance already exists, if so return the position
def instExists(node):
	cnt=0
	for n in nodes:
		if n.sir==node.sir and n.sir != '':
			return cnt;
		if n.instID==node.instID and node.ntype != "SPOTINSTANCEREQUEST" and n.instID!='':
			return cnt;
		cnt+=1
	return -1

# Asks the user a question and veryfies y/n by returning True or False
def confirmQuestion(Question):
	var=""
	while var != "y" and var != "n":
		var = raw_input(Question + " (y/n):" )
	if var == "y":
		return True
	else:
		return False
