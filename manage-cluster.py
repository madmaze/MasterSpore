#!/usr/bin/python

import os
import sys
import time
import CLnode
import GF
import getopt
		

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
		
		res = GF.run("ec2-request-spot-instances " + ami + " -p " + str(maxPrice) + " -instance-type " + inst_size + " -n " + str(nodecnt) + " --type one-time" + " --key " + keyName)
		if res.find("timeout")>=0:
			print "TIMEOUT: ", res
			return -1
		if res.find("InvalidAMIID")>=0:
			print "INVALID AMI ID: ", res
			return -1
		print res
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
				nodes.append(CLnode.CLnode(inst[1],inst[1],inst[5],inst[2],inst[6],inst[9],inst[10],inst[0],inst[3]))
	except Exception as x:
		print x, "\n", res
		return -1
	GF.addNewNodes(nodes)
	
	#ec2-describe-spot-instance-requests
def getSpotRequests():
	try:
		res = GF.run("ec2-describe-spot-instance-requests")
		if res.find("timeout")>=0:
			print "TIMEOUT: ", res
			return -1
		for line in res.split("\n"):
			if line.find("INSTANCE")>=0:
				inst=line.split("\t")
				GF.reqests.append(CLnode.CLnode(inst[1],inst[1],inst[5],'','','',inst[6],inst[0]))
	except Exception as x:
		print x, "\n", res
		return -1
		
def buildBundle(payload, payloadDir):
	try:
		#RM old bundle
		res=GF.run("rm "+payload)
		GF.log("rm "+payload,1)
		#make new bundle
		res=GF.run("tar cvf "+payload+' '+payloadDir+"/*")
		GF.log("tar cvf "+payload+' '+payloadDir+"/*",1)
	except Exception as x:
		print x, "\n", res
		sys.exit()

def monitor(n, timeout):
	allStarted=True
	
	for i in range(0,n):
		allStarted=True
		getSpotRequests()
		#getRunningInstances()
		for n in GF.requests:
			if n.status=="open":
				allStarted=False
		if allStarted is True:
			break
		time.sleep(timeout)
	if allStarted is False:	
		print "All instances did not start during designated time."
		if GF.confirmQuestion("Would you like to continue?") is True:
			monitor(n, timeout)
		else:
			sys.exit()
	else:
		for i in range(0,n):
			allStarted=True
			getRunningInstances()
			for n in GF.nodes:
				if n.status=="pending":
					allStarted=False
			if allStarted is True:
				break
		if allStarted is False:
			print "All instances did not start during designated time."
			if GF.confirmQuestion("Would you like to continue?") is True:
				monitor(n, timeout)
			else:
				sys.exit()
		else:
			#launch?!
			print "stuff"
			
	

if __name__ == "__main__":
	ami="ami-06ad526f"
	size="t1.micro"
	key="id_rsa"
	maxPrice=.01
	sshKey='/home/madmaze/.ec2/pkey'
	rebuildBundle=True
	payload='./bundle.tar'
	payloadDir='./payload'
	print "Cluster manager v0.1";
	argc=0
	for arg in sys.argv[1:]:
		argc+=1
		if arg == "-debug":
			GF.logLevel=2
		if arg == "-info":
			GF.logLevel=1
		if arg == "-list" or arg == "-l":
			getRunningInstances()
			cnt=0
			for node in GF.nodes:
				if node.running() is True:
					cnt+=1
				node.desc()
			GF.log("There are a totoal of "+str(cnt)+" instances running.",0)
			sys.exit()
		if arg == "-listblock" or arg == "-lb":
			getRunningInstances()
			cnt=0
			for node in GF.nodes:
				if node.running() is True:
					cnt+=1
				node.desc_detail()
			GF.log("There are a totoal of "+str(cnt)+" instances running.",0)
			sys.exit()
		if arg == "-listspots" or arg == "-ls":
			getSpotRequests()
			runcnt=0
			ocnt=0
			for node in GF.reqests:
				if node.status == "active":
					runcnt+=1
				if node.status == "open":
					ocnt+=1
				node.desc()
			GF.log("There are a totoal of "+str(runcnt)+" active and "+str(ocnt)+" waiting to launch",0)
			sys.exit()
		if arg == "-launch" and len(sys.argv) >= argc+2:
			try:
				n=int(sys.argv[argc+1])
				if n > 0:
					if GF.confirmQuestion("This will create "+str(n)+" instance(s). \nAre you sure you want to continue?") is False:
						sys.exit()
					print "Launching "+str(n)+" instances"
					launchCluster(ami, size, key, maxPrice, n)
				else:
					print "Please specify positive number"
				
			except Exception as x:
				print "Please specify number after -launch"
				print x, sys.argv[argc+1]
			sys.exit()
		if arg == "-shutdown" or arg == "-killall":
			# ask user for confirm
			if GF.confirmQuestion("!!This will TERMINATE all running instances!! \nAre you sure you want to continue?") is False:
				sys.exit()
			getRunningInstances()
			if len(GF.nodes)==0:
				print "There are currently no nodes to kill"
			for n in GF.nodes:
				n.kill()
		if arg == "-kill":
			# ask user for confirm
			foundinst=False
			getRunningInstances()
			if len(sys.argv) >= argc+2:
				var=sys.argv[argc+1].strip()
			else:
				var = raw_input("Which host would you like to deploy?: ").strip()

			for n in GF.nodes:
				if n.instName==var:
					foundinst=True
			if foundinst is False:
				print "There is currently no running instance by the ID: "+var
			else:
				if GF.confirmQuestion("!!This will kill the instance: "+var+"!\nAre you sure you want to continue?") is False:
					sys.exit()
				for n in GF.nodes:
					if n.instName==var:
						n.kill()
		if arg == "-deploy":
			# ask user for confirm
			foundinst=False
			getRunningInstances()
			if len(sys.argv) >= argc+2:
				var=sys.argv[argc+1].strip()
			else:                       
				var = raw_input("Which host would you like to deploy?: ").strip()
			
			for n in GF.nodes:
				if n.instName==var and n.status=='running':
					foundinst=True
			if foundinst is False:
				print "There is currently no running instance by the ID: "+var
			else:
				if GF.confirmQuestion("!!This will deploy on the instance: "+var+"!\nAre you sure you want to continue?") is False:
					sys.exit()
				if rebuildBundle is True:
					print "Building Bundle..."
					buildBundle(payload, payloadDir)
				for n in GF.nodes:
					if n.instName==var:
						n.deploy(payload,sshKey,True)
		if arg == "-monitor":
			monitor(10,10)
	
	#ec2-describe-images -a | grep ami-06ad526f
	#getRunningInstances()
	#launchCluster("ami-06ad526f", "t1.micro", "id_rsa", .01, 10)
