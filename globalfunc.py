#######################
# 0 = none
# 1 = info
# 2 = debug
logLevel=0
######################

def run(cmd):
	f=os.popen(cmd)
	buf=""
	for i in f.readlines():
		buf+=i
	return buf.strip()

def log(msg, lvl):
	if logLevel >= lvl:
		print msg
