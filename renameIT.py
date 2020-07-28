import os, subprocess, sys, argparse, re

# Get a list of file names
def get_fileNames(aDirectory):
	a = subprocess.Popen('ls %s' % aDirectory, stdout=subprocess.PIPE, shell=True)
	outputA,errorA = a.communicate()
	outputA = outputA.decode('utf-8')

	# Check for special characters in the names
	check = re.compile('[@!#$%^&*()<>?/\|}{~:]')
	if(check.search(outputA) == None):
		print("Creating file name list..")
		fileList1 = outputA.splitlines()
		return fileList1
	else:
		print("ERROR: File names cannot contain special characters:")
		fileList = outputA.splitlines()
		for x in fileList:
			if(check.search(x) != None):
				print(x)
		print("exiting..")
		sys.exit()	


# Find which files contain strings in named directory
def get_StringLists(aFileList, aDirectory):
	hasStrings = []
	noStrings = []
	index = 0
	for x in aFileList:
		tmpString = aDirectory + "/" + x
		b = subprocess.Popen('grep -a "const-string" %s' % tmpString, stdout=subprocess.PIPE, shell=True)
		outputTemp, errorTemp = b.communicate()
		outputTemp = outputTemp.decode('utf-8')
	
		# If no strings in file
		if not outputTemp:
			#print("No strings in file: ", x)
			noStrings.append(x)
		else:
			#print("Strings in file:  ", x)
			hasStrings.append(x)
			
			# Create dictionary item
			

		# Reset temp string
		tmpString = ""
	
	return hasStrings, noStrings

# Print output
#print("The following files contain strings:")
#print(hasStrings)

#print("The following file do not contain any strings:")
#print(noStrings)


# Start finding matches for the hasStrings list
#for x in hasStrings:
#	c = subprocess.Popen('grep -a "const-string" instantcoffee_named/%s.smali' % x, stdout=subprocess.PIPE, shell=True)
#	outputTempC, errorTempC = c.communicate()
#	outputTempC = outputTempC.decode('utf-8')
#	outputTempC = outputTempC.splitlines()



def main():
	#aDirectory = ""
	#parser = argparse.ArgumentParser(description='A program for renaming similar APKs')
	
	namedFileList = get_fileNames('instantcoffee_named')
	unnamedFileList = get_fileNames('instantcoffee_unnamed')
	
	namedHasStrings, namedNoStrings = get_StringLists(namedFileList, 'instantcoffee_named')
	unnamedHasStrings, unnamedNoStrings = get_StringLists(unnamedFileList, 'instantcoffee_unnamed')

	file1 = {
		"Name": namedHasStrings[0],
		"no_of_strings": len(namedHasStrings[0])
		}
	
	print(file1)


if __name__ == "__main__":
	main()













