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
		
def addNewNodes(new):
	for n in new:
		exists=instExists(n)
		if exists>=0:
			nodes[exists]=n.copy()
		else:
			nodes.append(n)
				
def instExists(node):
	cnt=0
	for n in nodes:
		if n.instID==node.instID:
			return cnt;
		cnt+=1
	return -1
	
def confirmQuestion(Question):
	var=""
	while var != "y" and var != "n":
		var = raw_input(Question + " (y/n):" )
		print var
	if var == "y":
		return True
	else:
		return False
		
