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
			sys.exit()
		cost=0
		for i in res.split("\n"):
			cost += float((i.split("\t"))[1]);
		cost = cost/len(res.split("\n"))
	except Exception as x:
		print x, "\n", res
		sys.exit()
	GF.log("Current Instance Cost: "+str(cost), 1);
	return cost

def startNodes(ami, inst_size, keyName, maxPrice, nodecnt):
	GF.log("... starting " + str(nodecnt) + " node(s)", 1);
	try:
		#res = GF.run("ec2-request-spot-instances " + ami + " -p " + maxPrice)
		
		res = GF.run("ec2-request-spot-instances " + ami + " -p " + str(maxPrice) + " -instance-type " + inst_size + " -n " + str(nodecnt) + " --type one-time" + " --key " + keyName)
		if res.find("timeout")>=0:
			print "TIMEOUT: ", res
			sys.exit()
		if res.find("InvalidAMIID")>=0:
			print "INVALID AMI ID: ", res
			sys.exit()
		print res
	except Exception as x:
		print x, "\n", res
		sys.exit()

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

def launchMaster(ami, inst_size, keyName):
	GF.log("Launching Master node..",1)
	try:
		res = GF.run("ec2-run-instances " + ami + " -k " + keyName + " -t " + size)
		if res.find("InvalidAMIID")>=0:
			print "INVALID AMI ID: ", res
			sys.exit()
		print res
		i=0
		lines=res.split("\n")
		master=CLnode.CLnode()
		for l in lines:
			inst=l.split("\t")
			for n in l.split("\t"):
				print i,n
				i+=1
			if inst[0]=="INSTANCE":
				master = CLnode.CLnode(inst[1],"MASTER",inst[5],inst[2],inst[6],inst[9],inst[10],inst[0],'',True)
		master.desc_detail()	
	except Exception as x:
		print x, "\n", res
		sys.exit()

def saveState():
	fname="./nodeDB"
	FILE = open(fname,"w")
	for n in GF.nodes:
		FILE.write(str(n)+"\n")
	FILE.close()

def loadState():
	try:
		fname="./nodeDB"
		FILE = open(fname,"r")
		while FILE:
			line = FILE.readline().strip().split(",")
			if len(line)<=1:
				break
			GF.nodes.append(CLnode.CLnode(*line))
			#line[0],line[1],line[2],line[3],line[4],line[5],line[6],line[7],line[8],line[9]
		FILE.close()
	except IOError:
		print "warning, nodeDB does not exists yet"
	except Exception as x:
		print x, "\n", res
		sys.exit()

def getRunningInstances():
	nodes = []
	try:
		res = GF.run("ec2-describe-instances")
		if res.find("timeout")>=0:
			print "TIMEOUT: ", res
			sys.exit()
		for line in res.split("\n"):
			if line.find("INSTANCE")>=0:
				inst=line.split("\t")
				nodes.append(CLnode.CLnode(inst[1],inst[1],inst[5],inst[2],inst[6],inst[9],inst[10],inst[0],inst[3],'',inst[22]))
	except Exception as x:
		print x, "\n", res
		sys.exit()
	GF.addNewNodes(nodes)
	
	#ec2-describe-spot-instance-requests
def getSpotRequests():
	try:
		res = GF.run("ec2-describe-spot-instance-requests")
		if res.find("timeout")>=0:
			print "TIMEOUT: ", res
			sys.exit()
		for line in res.split("\n"):
			if line.find("INSTANCE")>=0:
				inst=line.split("\t")
				GF.reqests.append(CLnode.CLnode(inst[1],inst[1],inst[5],'','','',inst[6],inst[0],''))
				GF.nodes.append(CLnode.CLnode('','slave',inst[5],'','','',inst[6],inst[0],'','',inst[1]))
	except Exception as x:
		print x, "\n", res
		sys.exit()
		
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
	try:
		opts, args = getopt.getopt(sys.argv[1:], "dil", ["debug", "info", "list", "listspots", "listblock", 
		"launch=", "shutdown", "killall", "kill=","deploy=","master="])
        except getopt.GetoptError, err:
		# print help information and exit:
		print str(err) # will print something like "option -a not recognized"
		sys.exit(2)

	output = None
        verbose = False
        loadState()
        for o, a in opts:
		if o in ("-d", "--debug"): 
			GF.logLevel=2
		elif o in ("-i", "--info"):
			GF.logLevel=1
		elif o in ("-l", "--list"):
			getRunningInstances()
			cnt=0
			for node in GF.nodes:
				if node.running() is True:
					cnt+=1
				node.desc()
			GF.log("There are a total of "+str(cnt)+" instances running.",0)
			saveState()
			sys.exit()  
		elif o in ("--listblock"):
			getRunningInstances()
			cnt=0
			for node in GF.nodes:
				if node.running() is True:
					cnt+=1
				node.desc_detail()
			GF.log("There are a totoal of "+str(cnt)+" instances running.",0)
			saveState()
			sys.exit()
		elif o in ("--listspots"):
			getSpotRequests()
			runcnt=0
			ocnt=0
			for node in GF.reqests:
				if node.status == "active":
					runcnt+=1
				if node.status == "open":
					ocnt+=1
				node.desc()
			GF.log("There are a total of "+str(runcnt)+" active and "+str(ocnt)+" waiting to launch",0)
			saveState()
			sys.exit()
		elif o in ("--master"):
			withlaunch=False
			for o2, a2 in opts:
				if o2 in ("--launch"):
					withlaunch=True
			if withlaunch is False:
				if GF.confirmQuestion("This will create a master node of size "+a2+" \nAre you sure you want to continue?") is False:
							sys.exit()
				launchMaster(ami,a,key)
			saveState()
		elif o in ("--launch"):
			#TODO: integrate MASTER
			for o2, a2 in opts:
				if o2 in ("--master"):
					if GF.confirmQuestion("This will create a master node of size "+a2+" \nAre you sure you want to continue?") is False:
							sys.exit()
					launchMaster(ami,a2,key)
			saveState() #save incase something fails
			if  len(a.split(',')) == 2:
				cnt=a.split(',')[0]
				size=a.split(',')[1]
				try:
					n=int(cnt)
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
				saveState()
				sys.exit()
			else:
				print "Please specify in the following fashion --launch=<N>,<inst size>"
		elif o in ("--shutdown","--killall"):
			# ask user for confirm
			if GF.confirmQuestion("!!This will TERMINATE all running instances!! \nAre you sure you want to continue?") is False:
				sys.exit()
			getRunningInstances()
			if len(GF.nodes)==0:
				print "There are currently no nodes to kill"
			for n in GF.nodes:
				n.kill()
			saveState()
		elif o in ("--kill"):
			foundinst=False
			getRunningInstances()
			if len(a) >= 6:
				var=a .strip()
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
			saveState()
		elif o in ("--deploy"):
			# ask user for confirm
			foundinst=False
			getRunningInstances()
			if len(a) >= 6:
				var=a .strip()
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
			saveState()
		else:
			assert False, "unhandled option"
		
			
	#ec2-describe-images -a | grep ami-06ad526f
	#getRunningInstances()
	#launchCluster("ami-06ad526f", "t1.micro", "id_rsa", .01, 10)
