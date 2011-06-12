import CLnode
import GF

for n in range(0,10):
	GF.nodes.append(CLnode.CLnode(str(n),str(n),str(n),str(n)))

n2=[]

for n in range(0,15):
	n2.append(CLnode.CLnode(str(n),str(n),str(n),str(n)))
	
GF.addNewNodes(n2)

for n in GF.nodes:
	n.desc()
