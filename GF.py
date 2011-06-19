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

def run(cmd):
	f=os.popen(cmd)
	buf=""
	for i in f.readlines():
		buf+=i
	return buf.strip()

def log(msg, lvl):
	if logLevel >= lvl:
		print msg

def str2bool(v):
	if type(v) is type(bool):
		return v
	else:
		return str(v).lower() in ("True", "true", "t", "1")
		
def addNewNodes(new):
	#TODO: reverse checking check whether there are instances 
	#      that are not running or in exsistance anymore
	print "adding",len(new)
	for n in new:
		exists=instExists(n)
#		if n.status == "terminated":
#			print "will be dropped: terminated ",str(n)
		if exists>=0:
			#nodes[exists].status=n.status
			#nodes[exists].url=n.url
			#nodes[exists].date=n.date
			#nodes[exists].instID=n.instID
			#nodes[exists].ntype=n.ntype
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
				
def instExists(node):
	cnt=0
	for n in nodes:
		if n.sir==node.sir and n.sir != '':
			return cnt;
		if n.instID==node.instID and node.ntype != "SPOTINSTANCEREQUEST" and n.instID!='':
			return cnt;
		cnt+=1
	return -1
	
def confirmQuestion(Question):
	var=""
	while var != "y" and var != "n":
		var = raw_input(Question + " (y/n):" )
	if var == "y":
		return True
	else:
		return False
		
