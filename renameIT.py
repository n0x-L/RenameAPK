import os, subprocess, sys, argparse, re, collections, pprint


# Methods 

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
			"guessed_name" : "unknown",
			"strings": strings,
			"unique_file_strings" : [],
			"unique_lib_strings" : []
			}
	
			#print(tmpDict["strings"][0])
			strings_chainMap = strings_chainMap.new_child(tmpDict)
			#chain2 = strings_chainMap.new_child(tmpDict)


		# Reset temp string
		tmpDirectory = ""
	
	return hasStrings, noStrings, strings_chainMap

# Use precense of unique library strings to make preliminary guesses
def unique_StringFinder(unnamed_strings_chain, named_strings_chain):
	tmpString = ""
	total_unique_fStrings = []

	# For each unnamed file extract the strings unique to that file
	for x in unnamed_strings_chain.maps:
		if x.get('Filename') != None:
			fileStringList = x.get('strings')

			# for each string in the file
			for aString in fileStringList:
				tmpString = tmpString + aString # concatenate together in order to use regex to pull out the strings

			tmpList = re.findall('"([^"]*)"', tmpString) # pull out the strings from the file into a list
			occurencesUnnamed = collections.Counter(tmpList) # count the occurences of each string in the file
			tmpString = ""

			# Check the occurences of the string in the file, if it is only once then add it to the list
			# of unique file strings
			for y in occurencesUnnamed:
				if occurencesUnnamed[y] == 1:
					z = x.get('unique_file_strings')
					z.append(y) # append the string to the unique file strings list

					if y not in total_unique_fStrings:
						total_unique_fStrings.append(y) # append the string to the total unique file strings list
						z = x.get('unique_lib_strings')
						z.append(y)


			#print(x.get('Filename') + ' unique_lib_strings: ')
			#print(x.get('unique_lib_strings'))

	return unnamed_strings_chain


# Try to find file matches based off of string matches
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

				# if strings array of x is the same as string array of guess z
				if tmpX == tmpZ:
					#print('Guess is that ' + x.get('Filename') + " is " + z.get('Filename'))
					x.update(guessed_name = z.get('Filename'))
					break

				if x.get('no_of_strings') >= 2:
					inList = 0
					notInList = 0
					for v in tmpX: # for each string in the file x string list
						if v in tmpZ: # if that string is in the guess z file string list
							#print('Maybe ' + x.get('Filename') + " is " + z.get('Filename') + " since '" + v + "' is in " + z.get('Filename'))
							inList+=1
						else:
							notInList+=1
					if inList > notInList:
						#print('*Guess is that ' + x.get('Filename') + " is " + z.get('Filename'))
						x.update(guessed_name = z.get('Filename'))

	
			# Reset list
			guesses = []

	return unnamed_strings_chain
		

#def confirm_Matches(guesses):
	# TO-DO

def main():
	#aDirectory = ""
	#parser = argparse.ArgumentParser(description='A program for renaming similar APKs')
	
	namedFileList = get_fileNames('library_named')
	unnamedFileList = get_fileNames('library_unnamed')
	
	namedHasStrings, namedNoStrings, named_strings_chain = get_StringLists(namedFileList, 'library_named')
	unnamedHasStrings, unnamedNoStrings, unnamed_strings_chain = get_StringLists(unnamedFileList, 'library_unnamed')
	
	unnamed_stringUnique_chain = unique_StringFinder(unnamed_strings_chain, named_strings_chain)

	
	unnamed_stringMatches_chain = string_Matching(unnamed_stringUnique_chain, named_strings_chain)

	pprint.pprint(unnamed_stringMatches_chain)

	#for x in unnamed_stringUnique_chain.maps:
	#	pprint.pprint(x)


if __name__ == "__main__":
	main()













