#!/usr/bin/python
########################################################
# masterSpore.py - MasterSpore
# This is a quick python tool that lets you launch and control a
# cluser of machines on AMAZON's EC2
#
# This tool allows you to:
# 1. launch a cluster consisting of
#    1 Master node and <N> slave nodes
#    The master node is requested as a normal instance for stability.
#    The slave nodes are launched as SpotInstances at a current market bid.
# 2. deploy a package/bundle of code/scripts/executables on each slave node
# 3. deploy/setup the master separately from the slaves <TODO>
# 4. collect logs from a central location on each of the slave nodes <TODO>
# 5. monitor/kill all nodes
#
# All code associate with this project is available under GPL v3
# Please find your copy here http://www.gnu.org/licenses/gpl-3.0.txt
# Copyright 2011 Matthias Lee
########################################################
import os
import sys
import time
import CLnode
import GF
import getopt
		
# Resolves current or most recent SpotInstance price for the specified inst_size
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

# Sarts <nodecnt> nodes with the given parameters
# does simple error checking to make sure nodes start
def startNodes(ami, inst_size, keyName, maxPrice, nodecnt):
	GF.log("... starting " + str(nodecnt) + " node(s)", 1);
	local=[]
	try:		
		res = GF.run("ec2-request-spot-instances " + ami + " -p " + str(maxPrice) + " -instance-type " + inst_size + " -n " + str(nodecnt) + " --type one-time" + " --key " + keyName)
		lines=res.split("\n")
		for i in range(0,len(res.split("\n"))):
			line=lines[i]
			print "res: ",i,line
			if line.find("SPOTINSTANCEREQUEST")>=0:
				inst=line.split("\t")
				local.append(CLnode.CLnode( ''    ,'slave' ,inst[5], ''  ,  '' ,  ''  ,inst[6] ,inst[0],  ''   ,False,inst[1],False))
				                           #instID,instName,status , ami , key , size ,  date  , ntype ,  url  ,master,sir,deployed):

		if res.find("timeout")>=0:
			print "TIMEOUT: ", res
			sys.exit()
		if res.find("InvalidAMIID")>=0:
			print "INVALID AMI ID: ", res
			sys.exit()
		
	except Exception as x:
		print x, "\n", res
		sys.exit()
	GF.addNewNodes(local)

# Gets the current spot price and makes sure that your bid is above that price
# then calls startNodes() to get the action moving
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
	startNodes(ami, inst_size, keyName, maxPrice, nodes)

# Launches the master node with the given parameters
def launchMaster(ami, inst_size, keyName):
	GF.log("Launching Master node..",1)
	local=[]
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
			if inst[0]=="INSTANCE":
				master = CLnode.CLnode(inst[1],"MASTER",inst[5],inst[2],inst[6],inst[9],inst[10],inst[0],'',True)
		master.desc_detail()
		local.append(master)
		GF.addNewNodes(local)
	except Exception as x:
		print x, "\n", res
		sys.exit()

# Saves all current nodes/instances to a file which will be parsed
# on next startup to retain knowledge of the nodes metadata
def saveState():
	fname="./nodeDB"
	FILE = open(fname,"w")
	for n in GF.nodes:
		FILE.write(str(n)+"\n")
	FILE.close()

# Loads a dictionary file to scrape up meta-data associated with instances
# EX: is a node a Master or slave? has it been deployed?
def loadState():
	getRunningInstances()
	nodes=[]
	try:
		fname="./nodeDB"
		FILE = open(fname,"r")
		while FILE:
			line = FILE.readline().strip().split(",")
			if len(line)<=1:
				break
			nodes.append(CLnode.CLnode(*line))
			#line[0],line[1],line[2],line[3],line[4],line[5],line[6],line[7],line[8],line[9]
		FILE.close()
		GF.addNewNodes(nodes)
	except IOError:
		print "warning, nodeDB does not exists yet"
	except Exception as x:
		print x, "\n", res
		sys.exit()

# Gets a list of currently and recently run instances
def getRunningInstances():
	try:
		res = GF.run("ec2-describe-instances")
		if res.find("timeout")>=0:
			print "TIMEOUT: ", res
			sys.exit()
		for line in res.split("\n"):
			if line.find("INSTANCE")>=0:
				inst=line.split("\t")
				if inst[5] != "terminated":
					GF.nodes.append(CLnode.CLnode(inst[1],inst[1],inst[5],inst[2],inst[6],inst[9],inst[10],inst[0],inst[3],'',inst[22]))
				else:
					GF.log("found terminated"+line,2)
	except Exception as x:
		print x, "\n", res
		sys.exit()
	
# Gets the current list of SpotRequests and adds then to GF.requests
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
	except Exception as x:
		print x, "\n", res
		sys.exit()

# Tars up the payload directory
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

# Currently not in use, Future purpose is to track monitor
# until all nodes have launched, then deploy
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
	sshKey='~/.ec2/pkey'
	rebuildBundle=True
	payload='./bundle.tar'
	logsDir='./logs'
	payloadDir='./payload'
	print "Cluster manager v0.2";
	argc=0
	try:
		opts, args = getopt.getopt(sys.argv[1:], "dilh", ["help", "debug", "info", "list", "listspots", "listblock", 
		"launch=", "shutdown", "curSpotPrice", "deployall","gatherlogs", "killall", "kill=","deploy=","master="])
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
			cnt=0
			for node in GF.nodes:
				if node.running() is True:
					cnt+=1
				node.desc()
			GF.log("There are a total of "+str(cnt)+" instances running.",0)
			saveState()
			sys.exit()  
		elif o in ("--listblock"):
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
			if len(GF.nodes)==0:
				print "There are currently no nodes to kill"
			for n in GF.nodes:
				n.kill()
			saveState()
		elif o in ("--kill"):
			foundinst=False
			if len(a) >= 6:
				var=a .strip()
			else:
				var = raw_input("Which host would you like to deploy?: ").strip()

			for n in GF.nodes:
				if n.instID==var:
					foundinst=True
			if foundinst is False:
				print "There is currently no running instance by the ID: "+var
			else:
				if GF.confirmQuestion("!!This will kill the instance: "+var+"!\nAre you sure you want to continue?") is False:
					sys.exit()
				for n in GF.nodes:
					if n.instID==var:
						n.kill()
			saveState()
		elif o in ("--deploy"):
			# ask user for confirm
			foundinst=False
			if len(a) >= 6:
				var=a .strip()
			else:                       
				var = raw_input("Which host would you like to deploy?: ").strip()
			
			for n in GF.nodes:
				if n.instID==var and n.status=='running':
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
					if n.instID==var:
						n.deploy(payload,sshKey,True)
			saveState()
		elif o in ("--deployall"):
			
			if GF.confirmQuestion("!!This will deploy all Instances!\nAre you sure you want to continue?") is False:
				sys.exit()
			if rebuildBundle is True:
				print "Building Bundle..."
				buildBundle(payload, payloadDir)
			for n in GF.nodes:
				if n.status=='running':
					n.deploy(payload,sshKey,True)
			saveState()
		elif o in ("--gatherlogs"):
			lt = time.localtime(time.time())	
			#should be ddmmyyyy-hhmmss AKA should not allow single digits in time
			timestamp=str(lt[2])+str(lt[1])+str(lt[0])+"-"+str(lt[3])+":"+str(lt[4])+":"+str(lt[5])
			if GF.confirmQuestion("!!This will gather up all logs from agents and master!\nAre you sure you want to continue?") is False:
				sys.exit()
			for n in GF.nodes:
				if n.status=='running':
					n.gather(logsDir+"/"+timestamp,sshKey)
			saveState()
		elif o in ("--curSpotPrice"):
			print "Resolving current Spot Price for", a,"instances.. please wait."
			print "\n"
			print "Current Price:", curSpotCost(a), "$"
			saveState()
		elif o in ("--help"):
			print 	"Help:\n"
			print	"./masterSpore.py --help - help menu"
			print	"./masterSpore.py -d - enable debug output" 
			print	"./masterSpore.py -l - List all entires"
			print   "./masterSpore.py --curSpotPrice <spot-size> - looks up current spot price"
			print	"./masterSpore.py --killall - kills all nodes/instances currently associated with your account"
			print	"./masterSpore.py --kill <inst-id> - kills a specific instance, use -l to find the inst-id"
			print	"./masterSpore.py --master <inst-size> - this will create a master node/instance which will not be a spot instance"
			print	"./masterSpore.py --launch <N>,<spot-size> - where N is the number of nodes/instances and spot-size is the spot-inst request size"
			print	"\n\nSpot/Inst sizes: t1.micro, m1.small etc etc.."
		else:
			assert False, "unhandled option\n try: --help"
	if len(opts) == 0:
		print "No provided options.. try: --help"
