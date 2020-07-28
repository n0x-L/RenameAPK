import os, subprocess, sys, argparse

userid = "ck"
p = subprocess.Popen('grep -a "const-string" instantcoffee_named/%s.smali' % userid, stdout=subprocess.PIPE, shell=True)
output,error = p.communicate()
#print(output)

# decode bytes to string
#print("decoding..")
output = output.decode('utf-8')
#print(output)

# Make a list
stringList = output.splitlines()
thing1 = stringList[0]

# Get other matching file
b = subprocess.Popen('grep -a "const-string" instantcoffee_unnamed/cm.smali', stdout=subprocess.PIPE, shell=True)
output2,error2 = b.communicate()
output2 = output2.decode('utf-8')
stringList2 = output.splitlines()
thing2 = stringList2[0]



i = 0
for x in stringList:
	if x != stringList2[i]:
		print("These don't match!")
		print(x)
		print(stringList2[i])
	else:
		print("They match!")
		print(x)
		print(stringList2[i])
	if i != len(stringList2):
		i = i + 1
