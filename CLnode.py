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
	
	def __init__(self, instID='',instName='',status='',ami='',key='',size='',date='',ntype='',url=''):
		self.instID=instID
		self.instName=instName
		self.status=status
		self.ami=ami
		self.key=key
		self.size=size
		self.date=date
		self.ntype=ntype
		self.url=url
	
	def kill(self):
		if self.status!="running":
			print "Instance is not running, therefore will not shutdown"
			return
		try:
			res=''
			res = GF.run("ec2-terminate-instances "+self.instID)
			print res
		except Exception as x:
			print x, "\n", res
			return -1
	
	def desc(self):
		print self.ntype,self.instID,self.instName,self.url,self.status,self.ami,self.key,self.size,self.date

	def desc_detail(self):
		print "Instance Type:\t\t"+self.ntype
		print "Instance ID:\t\t"+self.instID
		print "Instance Name:\t\t"+self.instName
		print "Status:\t\t\t"+self.status
		print "Hostname/url:\t"+self.url
		print "AMI:\t\t\t"+self.ami
		print "Keypair:\t\t"+self.key
		print "Instance Size:\t\t"+self.size
		print "Date/Time started:\t"+self.date
		print "===="

		
	
	def statys(self):
		return self.status
	
	def running(self):
		if self.status=="running":
			return True
		else:
			return False
	
	def copy(self):
		return CLnode(self.instID,self.instName,self.status,self.ami,self.key,self.size,self.date,self.ntype,self.url)
