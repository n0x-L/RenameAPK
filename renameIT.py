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

	# TO-DO
	# Check that all given filenames are unique!


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
			#strings = strings.splitlines()
			stringsList = re.findall('"([^"]*)"', strings) 

			tmpDict = {
			"Filename": x,
			"no_of_strings": len(stringsList),
			"new_name" : "unknown",
			"guessed_name" : "unknown",
			"strings": stringsList,
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
def unique_StringFinder(strings_chain):
	tmpString = ""
	total_unique_fStrings = []

	# For each unnamed file extract the strings unique to that file
	for x in strings_chain.maps:
		if x.get('Filename') != None:
			fileStringList = x.get('strings')

			# for each string in the file
			#for aString in fileStringList:
			#	tmpString = tmpString + aString # concatenate together in order to use regex to pull out the strings

			#tmpList = re.findall('"([^"]*)"', tmpString) # pull out the strings from the file into a list
			#occurencesUnnamed = collections.Counter(tmpList) # count the occurences of each string in the file
			#tmpString = ""

			occurencesUnnamed = collections.Counter(fileStringList) 

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

	return strings_chain


# Try to find file matches based off of string matches
def string_Matching(unnamed_strings_chain, named_strings_chain):
	i = 0
	guesses = []
	still_unknown = collections.ChainMap()

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
			if x.get('guessed_name') == 'unknown':
				uniqueLibStrings = x.get('unique_lib_strings')
				if uniqueLibStrings:
					#still_unknown.append(x)
					still_unknown = still_unknown.new_child(x)

	return unnamed_strings_chain, still_unknown

# Given a list of still currently unknown files with unique library strings for each file,
# try and determine based on the unique library string which file it likely is.
def unique_StringMatching(still_unknown, named_strings_chain, unnamed_strings_chain):
	for uFile in still_unknown.maps:
		if uFile.get('Filename') != None:
			uList = uFile.get('unique_lib_strings')

			#if uFile.get('Filename') == 'cm.smali':
			#	print('*******cm.smali unique strings: ')
			#	print(uFile.get('unique_lib_strings'))

			# Iterate over the named files to find a match
			for nFile in named_strings_chain.maps:
				if nFile.get('Filename') != None:
					nList = nFile.get('unique_lib_strings')

					# Generate a percentage value of how similar the two lists are
					evaluate = len(set(uList) & set(nList)) / float(len(set(uList) | set(nList))) * 100

					# Iterate over the unnamed files and assign 
					# guesses or matches based on how close the matches are
					# for the unique library strings list
					for oFile in unnamed_strings_chain.maps:
						if oFile.get('Filename') == uFile.get('Filename'):
							if evaluate == 100.0:
								oFile.update(guessed_name = nFile.get('Filename')) # if we have a new name then we have a guessed name
								oFile.update(new_name = nFile.get('Filename'))
							elif evaluate > 50.0:
								oFile.update(guessed_name = nFile.get('Filename'))
							else:
								continue
						
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
	
	# Fill out the 'unique_file_strings' and 'unique_lib_strings' portion of the data structure
	unnamed_uniqueStringsChain = unique_StringFinder(unnamed_strings_chain)
	named_uniqueStringsChain = unique_StringFinder(named_strings_chain)

	# Make some matches and get back any that couldn't be matched yet
	unnamed_stringMatchesChain, still_unknown = string_Matching(unnamed_uniqueStringsChain, named_uniqueStringsChain)

	print('\n---- Progress Update ---')
	all_unnamed_stringfilesCount = len(unnamedHasStrings)
	unknownCount = len(still_unknown.maps)
	knownCount = all_unnamed_stringfilesCount - unknownCount
	print('Total number of unnamed files: ' + str(all_unnamed_stringfilesCount))
	print('Number of (unconfirmed) guesses for files containing strings: ' + str(knownCount))
	print('Number of unknowns for files containing unique library strings: ' + str(unknownCount))
	print('\n continuing...')

	finalStringGuesses = unique_StringMatching(still_unknown, named_uniqueStringsChain, unnamed_stringMatchesChain)

	unknownCount = 0
	knownCount = 0
	print('\n--GUESSES--')
	for x in finalStringGuesses.maps:
		if x.get('Filename') != None:
			if x.get('guessed_name') != 'unknown':
				print(x.get('Filename') + ' is ' + x.get('guessed_name'))
				knownCount+=1
			else:
				print('Still not sure who "' + x.get('Filename') + '" is.')
				unknownCount+=1

	print('\n---- Progress Update ---')
	totalCount_unnamed = len(unnamedHasStrings) + len(unnamedNoStrings)
	print('Total number of unnamed files: ' + str(totalCount_unnamed))
	print('Total number of unnamed files containing strings: ' + str(len(unnamedHasStrings)))
	print('Number of (unconfirmed) guesses for files containing strings: ' + str(knownCount))
	print('Number of still unknowns for files containing unique library strings: ' + str(unknownCount))
	print('\n continuing...')

	#uCount = 0
	#uuCount = 0
	#for x in unnamed_uniqueStringsChain.maps:
	#	if x.get('Filename') != None:
	#		if x.get('guessed_name') == 'unknown':
	#			if x.get('unique_lib_strings'):
	#				uuCount+=1
	#			print('Not sure who ' + x.get('Filename') + ' is.')
	#			uCount+=1
	#print('Number of unknowns counted: ' + str(uCount))
	#print('Number of unknowns with unique lib strings counted: ' + str(uuCount))
		#pprint.pprint(x)

	#for x in still_unknown.maps:
	#	if x.get('guessed_name') == 'unknown':
	#		print('Not sure who ' + x.get('Filename') + ' is.')
	#		uCount+=1
	#print('Number of unknowns with unique lib strings counted: ' + str(uCount))


if __name__ == "__main__":
	main()













