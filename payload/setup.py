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
except Exception as x:
	print x, "\n", res
