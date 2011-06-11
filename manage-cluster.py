#!/usr/bin/python

import os
import sys
import time
import CLnode
import GF
		

def curSpotCost(inst_size):
	lt = time.localtime(time.time())	
	curdate = str(lt[0])+"-"+str(lt[1])+"-"+str(lt[2])+"T"+str(lt[3])+":"+str(lt[4])+":"+str(lt[5])+":"+str(lt[6])+"-0000"
	try:
		res = GF.run("ec2-describe-spot-price-history -d Linux/UNIX --region us-east-1 --instance-type "+inst_size+" -s "+curdate)
		if res.find("timeout")>=0:
			print "TIMEOUT: ", res
			return -1
		cost=0
		for i in res.split("\n"):
			cost += float((i.split("\t"))[1]);
		cost = cost/len(res.split("\n"))
	except Exception as x:
		print x, "\n", res
		return -1
	GF.log("Current Instance Cost: "+str(cost), 1);
	return cost

def startNodes(ami, inst_size, keyName, maxPrice, nodecnt):
	GF.log("... starting " + str(nodecnt) + " node(s)", 1);
	try:
		#res = GF.run("ec2-request-spot-instances " + ami + " -p " + maxPrice)
		res = ""
		print "ec2-request-spot-instances " + ami + " -p " + str(maxPrice) + " -instance-type " + inst_size + " -n " + str(nodecnt) + " --type one-time" + " --key " + keyName
		if res.find("timeout")>=0:
			print "TIMEOUT: ", res
			return -1
		if res.find("InvalidAMIID")>=0:
			print "INVALID AMI ID: ", res
			return -1
	except Exception as x:
		print x, "\n", res
		return -1

def launchCluster(ami, inst_size, keyName, maxPrice, nodes):
	GF.log("Maximum Price: "+str(maxPrice), 1);
	curPrice=curSpotCost(inst_size)
	if curPrice == -1:
		print "Error: Failed to get current spot price."
		sys.exit(-1)
	if curPrice > maxPrice:
		print "Error: Current spot price too high."
		sys.exit(-2)
	GF.log("Launching "+str(nodes)+" nodes.", 1);
	#for n in range (0,nodes):
	startNodes(ami, inst_size, keyName, maxPrice, nodes)

def getRunningInstances():
	nodes = []
	try:
		res = GF.run("ec2-describe-instances")
		if res.find("timeout")>=0:
			print "TIMEOUT: ", res
			return -1
		for line in res.split("\n"):
			if line.find("INSTANCE")>=0:
				inst=line.split("\t")
				nodes.append(CLnode.CLnode(inst[1],inst[1],inst[5],inst[2],inst[6],inst[9],inst[10]))
				print len(nodes)
	except Exception as x:
		print x, "\n", res
		return -1
		
	for node in nodes:
		node.desc()

	
if __name__ == "__main__":
	for arg in sys.argv[1:]:
		if arg == "-debug":
			GF.logLevel=2
		if arg == "-info":
			GF.logLevel=1
	GF.log("Starting cluster manager...", 1);
	#ec2-describe-images -a | grep ami-06ad526f
	getRunningInstances()
	#launchCluster("ami-06ad526f", "t1.micro", "id_rsa", .01, 10)
