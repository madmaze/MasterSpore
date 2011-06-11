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
	
	def __init__(self, instID='',instName='',status='',ami='',key='',size='',date=''):
		self.instID=instID
		self.instName=instName
		self.status=status
		self.ami=ami
		self.key=key
		self.size=size
		self.date=date
	
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
		print self.instID,self.instName,self.status,self.ami,self.key,self.size,self.date

