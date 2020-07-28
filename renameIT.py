import os, subprocess, sys, argparse, re, collections

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


# Find which files contain strings in named directory and return appropriate values
def get_StringLists(aFileList, aDirectory):
	hasStrings = []
	noStrings = []
	index = 0
	strings_chainMap = collections.ChainMap()

	for x in aFileList:
		tmpDirectory = aDirectory + "/" + x
		b = subprocess.Popen('grep -a "const-string" %s' % tmpDirectory, stdout=subprocess.PIPE, shell=True)
		strings, errorTemp = b.communicate()
		strings = strings.decode('utf-8')
	
		# If no strings in file
		if not strings:
			#print("No strings in file: ", x)
			noStrings.append(x)
		else:
			#print("Strings in file:  ", x)
			hasStrings.append(x)

			# Put strings into a list
			strings = strings.splitlines()

			tmpDict = {
			"Filename": x,
			"no_of_strings": len(strings),
			"new_name" : "unknown",
			"strings": strings
			}
	
			#print(tmpDict["strings"][0])
			strings_chainMap = strings_chainMap.new_child(tmpDict)
			#chain2 = strings_chainMap.new_child(tmpDict)


		# Reset temp string
		tmpDirectory = ""
	
	return hasStrings, noStrings, strings_chainMap

# Try to find string matches

def string_Matching(unnamed_strings_chain, named_strings_chain):
	i = 0
	guesses = []

	for x in unnamed_strings_chain.maps:
		if x.get('Filename') != None:
			for y in named_strings_chain.maps:
				if x.get('no_of_strings') == y.get('no_of_strings'):
					guesses.append(y)

			for z in guesses:
				tmpX = x.get('strings')
				tmpZ = z.get('strings')

				if tmpX == tmpZ:
					print('Guess is that ' + x.get('Filename') + " is " + z.get('Filename'))
					break

					# send guesses to confirm method
					

			#print("Guesses for " + x.get('Filename'))
			#print(guesses)

			# Reset list
			#guesses = []

def confirm_Matches(guesses):
	# TO-DO

def main():
	#aDirectory = ""
	#parser = argparse.ArgumentParser(description='A program for renaming similar APKs')
	
	namedFileList = get_fileNames('instantcoffee_named')
	unnamedFileList = get_fileNames('instantcoffee_unnamed')
	
	namedHasStrings, namedNoStrings, named_strings_chain = get_StringLists(namedFileList, 'instantcoffee_named')
	unnamedHasStrings, unnamedNoStrings, unnamed_strings_chain = get_StringLists(unnamedFileList, 'instantcoffee_unnamed')
	
	string_Matching(unnamed_strings_chain, named_strings_chain)
	#print(named_strings_chain.maps)


if __name__ == "__main__":
	main()













