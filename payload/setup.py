import os
import sys

def run(cmd):
	f=os.popen(cmd)
	buf=""
	for i in f.readlines():
		buf+=i
	return buf.strip()

try:
	res=run("touch ~/TEST")
	res=run("mkdir -p /var/tmp/log")
	res=run("ifconfig > /var/tmp/log/conifg")
except Exception as x:
	print x, "\n", res
