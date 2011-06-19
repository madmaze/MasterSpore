import os
import sys
import GF

class CLnode:
	instID=''
	instName=''
	status=''
	ami=''
	key=''
	size=''
	date=''
	ntype=''
	url=''
	master=False
	sir=''
	deployed=False
	
	def __init__(self, instID='',instName='',status='',ami='',key='',size='',date='',ntype='',url='',master=False,sir='',deployed=False):
		self.instID=instID
		self.instName=instName
		self.status=status
		self.ami=ami
		self.key=key
		self.size=size
		self.date=date
		self.ntype=ntype
		self.url=url
		self.master=GF.str2bool(master)
		self.sir=sir
		self.deployed=GF.str2bool(deployed)
	
	def kill(self):
		if self.status!="running":
			print "Instance is not running, therefore will not shutdown"
			return
		try:
			res=''
			res = GF.run("ec2-terminate-instances "+self.instID)
			print res
			self.status='terminated'
		except Exception as x:
			print x, "\n", res
			return -1
	
	
	def desc(self):
		print self.ntype,self.master,self.instID,self.instName,self.status,self.url,self.ami,self.key,self.size,self.date,self.sir,self.deployed

	def __repr__(self):
		return self.instID+","+self.instName+","+self.status+","+self.ami+","+self.key+","+self.size+","+self.date+","+self.ntype+","+self.url+","+str(self.master)+","+self.sir+","+str(self.deployed)
	
	def desc_detail(self):
		print "Instance Type:\t\t"+self.ntype
		print "Is Master Node:\t\t"+str(self.master)
		print "Has been deployed:\t"+str(self.deployed)
		print "Instance ID:\t\t"+self.instID
		print "Instance Name:\t\t"+self.instName
		print "Status:\t\t\t"+self.status
		print "Hostname/url:\t"+self.url
		print "AMI:\t\t\t"+self.ami
		print "Keypair:\t\t"+self.key
		print "Instance Size:\t\t"+self.size
		print "Date/Time started:\t"+self.date
		print "Spot Inst Request:\t"+self.sir
		print "===="

		
	
	def status(self):
		return self.status
	
	def running(self):
		if self.status=="running":
			return True
		else:
			return False
	
	def copy(self):
		return CLnode(self.instID,self.instName,self.status,self.ami,self.key,self.size,self.date,self.ntype,self.url,self.master,self.sir,self.deployed)
		
	def deploy(self,payload,sshKey,launch=False):
		# TODO: error handeling
		print "\n============================================"
		print "Deploing",self.instID,"/",self.instName
		print "====="
		
		if self.master is False:
			try:
				res=GF.run("scp -o StrictHostKeyChecking=no -i "+sshKey+" "+payload+"  ubuntu@"+self.url+":~/")
				print "scp -o StrictHostKeyChecking=no -i "+sshKey+" "+payload+"  ubuntu@"+self.url+":~/"
			except Exception as x:
				print x, "\n", res
				return -1
			
			# EXTRACT payload
			try:
				res=GF.run("ssh -o StrictHostKeyChecking=no -i "+sshKey+" ubuntu@"+self.url+" 'tar xvf ~/bundle.tar;'")
				print "ssh -o StrictHostKeyChecking=no -i "+sshKey+" ubuntu@"+self.url+" 'tar xvf ~/bundle.tar;'"
			except Exception as x:
				print x, "\n", res
				return -1
			
			if launch is True:
				# LAUNCH Payload
				try:
					res=GF.run("ssh -o StrictHostKeyChecking=no -i "+sshKey+" ubuntu@"+self.url+" 'python ~/payload/setup.py'")
					print "ssh -o StrictHostKeyChecking=no -i "+sshKey+" ubuntu@"+self.url+" 'python ~/payload/setup.py'"
					self.deployed = True
				except Exception as x:
					print x, "\n", res
					return -1
		else:
			print "Master node: No need to deploy!"
			
			
