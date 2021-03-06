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

		# Print out what the offending files are
		for x in fileList:
			if(check.search(x) != None):
				print(x)
		print("exiting..")
		sys.exit()	

	# TO-DO
	# Check that all given filenames are unique!

	# TO-DO
	# Method for renaming files with special characters since the dollar sign is such a common occurence with pro-guard
	# linux command: mv oldfile.txt newfile.txt

# For getting an update on how many files have had guesses applied to them
def get_Update(unnamedFileList, aChainMap):
	total_files = len(unnamedFileList)
	guesses_count = 0

	for x in aChainMap.maps:
		if x.get('Filename') != None:
			if x.get('guessed_name') != 'unknown':
				guesses_count += 1

	print(str(guesses_count) + ' / ' + str(total_files) + ' files guessed')

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
def string_Matching(named_strings_chain, unnamed_strings_chain):
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
				#if tmpX == tmpZ:
				if set(tmpX) == set(tmpZ):
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
	still_unknown2 = []
	for uFile in still_unknown.maps:
		if uFile.get('Filename') != None:
			uList = uFile.get('unique_lib_strings')

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

			# If there are still no guesses for the file, put it
			# in a collections to return and pass to the fields and 
			# methods matching/guesses functions
			if uFile.get('guessed_name') == 'unknown':
				still_unknown2.append(uFile.get('Filename'))
						
	return unnamed_strings_chain, still_unknown2

# Get fields and methods attributes for files which do not contain strings		
def get_FieldsAndMethods(aFileList, aDirectory, packageName):
	fields_methods_chainMap = collections.ChainMap()
	fieldsList = []
	methodsList = []

	# TO-DO insert packageName
	methods_re = re.compile('L' + packageName + '/[a-z_]*')

	for x in aFileList:
		tmpDirectory = aDirectory + "/" + x

		# Get fields
		b = subprocess.Popen('grep -a ".field " %s' % tmpDirectory, stdout=subprocess.PIPE, shell=True)
		fields, errorTemp = b.communicate()
		fields = fields.decode('utf-8')

		if fields:
			# Filter out field names (for package fields they will be differently named)
			tmpFieldsList = re.findall('((\\b)([a-zA-Z0-9_]+):(.)*$)', fields, flags=re.M)

			for y in tmpFieldsList:
				# There's no sense comparing objects in the package 
				# because the names will be different
				if packageName in y[0]:
					fieldsList.append(packageName)
				else:
					fieldsList.append(y[0])

		# Do a grep of the methods in the file
		c = subprocess.Popen('grep -a ".method " %s' % tmpDirectory, stdout=subprocess.PIPE, shell=True)
		methods, errorMTemp = c.communicate()
		methods = methods.decode('utf-8')
	

		# If methods in file, build a list of methods using a regex to extract them from the grep
		if methods:
			tmpMethodsList = re.findall('((\\b)([a-zA-Z0-9_]+)\((.)*$|constructor.*$)', methods, flags=re.M)
			
			# A bit trickier, use regex to replace "Linstantcoffee/x" occurences with just "instantcoffee"
			# while maintaining everything else so that we don't lose the form of the method signature
			for y in tmpMethodsList:
				if packageName in y[0]:
					methodsList.append(methods_re.sub(packageName, y[0]))
				else:
					methodsList.append(y[0])

		tmpDict = {
		"Filename": x,
		"no_of_fields": len(fieldsList),
		"fields" : fieldsList,
		"no_of_methods": len(methodsList),
		"methods" : methodsList,
		"new_name" : "unknown",
		"guessed_name" : "unknown"
		}

		fields_methods_chainMap = fields_methods_chainMap.new_child(tmpDict)

		# Reset values
		tmpDirectory = ""
		fieldsList = []
		methodsList = []
	
	return fields_methods_chainMap

# Take in dicts of information on fields and methods and do comparisons to try and make matches
# (similar method to the string matching method)
def fieldsAndMethods_Matching(named_fieldsAndMethods_chainMap, unnamed_fieldsAndMethods_chainMap):
	still_unknown3 = collections.ChainMap()

	for x in unnamed_fieldsAndMethods_chainMap.maps:
		if x.get('Filename') != None:
			# If they have the same number of fields AND methods then store it in the 'guesses' list
			for y in named_fieldsAndMethods_chainMap.maps:
				if x.get('no_of_fields') == y.get('no_of_fields') and x.get('no_of_methods') == y.get('no_of_methods'):
					tmpFieldsX = x.get('fields')
					tmpMethodsX = x.get('methods')
					tmpFieldsY = y.get('fields')
					tmpMethodsY = y.get('methods')

				# If fields array and methods array of x is the same as fields and methods array of guess z
				# then record it as the guess
					if set(tmpFieldsX) == set(tmpFieldsY) and set(tmpMethodsX) == set(tmpMethodsY):
						x.update(guessed_name = y.get('Filename'))
						y.update(guessed_name = x.get('Filename'))

						break # stop searching if match is found

			# At this point we will have checked the x file against all the 
			# y files, so if we found no matches for it, store
			# it in the uknown list and move on to the next x file
			if x.get('guessed_name') == 'unknown':
				still_unknown3 = still_unknown3.new_child(x)

	return unnamed_fieldsAndMethods_chainMap, named_fieldsAndMethods_chainMap, still_unknown3

# Try to make final guesses for files that we still aren't sure about
def fieldsAndMethods_Guessing(still_unknown3, named_fieldsAndMethods_chain, unnamed_fieldsAndMethods_chain):
	left_unknown = collections.ChainMap()
	evaluate_fields = 0.0
	evaluate_methods = 0.0

	for u2File in still_unknown3.maps:
		if u2File.get('Filename') != None:

			# Don't try to make estimates with files that have no fields 
			# or no methods because it won't be a good enough guess
			if u2File.get('no_of_fields') != 0 and u2File.get('no_of_methods') != 0:
				# Get the files fields and methods list
				u2_fieldsList = u2File.get('fields')
				u2_methodsList = u2File.get('methods')

				# Iterate over the named files to find a match
				for nFile in named_fieldsAndMethods_chain.maps:
					if nFile.get('Filename') != None and nFile.get('guessed_name') == 'unknown': # no point comparing to files that already have matches
						print("make a guess")
						# Get the named files fields and methods lists
						n_fieldsList = nFile.get('fields')
						n_methodsList = nFile.get('methods')

						# Generate a percentage value of how similar the two field lists are
						if float(len(set(u2_fieldsList) | set(n_fieldsList))) != 0:
							evaluate_fields = len(set(u2_fieldsList) & set(n_fieldsList)) / float(len(set(u2_fieldsList) | set(n_fieldsList))) * 100

						# Generate a percentage value of how similar the two methods lists are
						if float(len(set(u2_methodsList) | set(n_methodsList))) != 0:
							evaluate_methods = len(set(u2_methodsList) & set(n_methodsList)) / float(len(set(u2_methodsList) | set(n_methodsList))) * 100

					#if evaluate_fields > 0.0:
					#	print('Percentage simliarity of fields in file ' + u2File.get('Filename') + ' and ' + nFile.get('Filename') + ': ' + str(evaluate_fields))

					#if evaluate_methods > 0.0:
					#	print('Percentage simliarity of methods in file ' + u2File.get('Filename') + ' and ' + nFile.get('Filename') + ': ' + str(evaluate_methods))

					# Iterate over the unnamed files and assign 
					# guesses or matches based on how close the matches are
					# for the methods and fields lists
						for oFile in unnamed_fieldsAndMethods_chain.maps:
							if oFile.get('Filename') == u2File.get('Filename'): # find where in the unnamed list is the unknown file we're evaluating
								if evaluate_methods > 49.0 and evaluate_fields > 49.0:
									# Don't overwrite guesses we already made
									if oFile.get('guessed_name') == 'unknown':
										#print('making a guess')
										oFile.update(guessed_name = nFile.get('Filename'))
										break # stop looking, since we were just searching for the matching file to either update the guessed_name value or not
									#else:
										#print('already made a guess for ' + oFile.get('Filename'))
							else:
									#if evaluate_fields > 0.0 or evaluate_methods > 0.0:
									#	print('Not sure who ' + u2File.get('Filename') + ' is.')
									#	print('Percentage simliarity of fields in file ' + u2File.get('Filename') + ' and ' + nFile.get('Filename') + ': ' + str(evaluate_fields))
									#	print('Percentage simliarity of methods in file ' + u2File.get('Filename') + ' and ' + nFile.get('Filename') + ': ' + str(evaluate_methods))
								continue # keep searching for the matching file

					#left_unknown = left_unknown.new_child(File)
						
	return unnamed_fieldsAndMethods_chain, left_unknown


def main():
	#aDirectory = ""
	#parser = argparse.ArgumentParser(description='A program for renaming similar APKs')
	
	namedFileList = get_fileNames('library_named')
	unnamedFileList = get_fileNames('library_unnamed')
	
	namedHasStrings, namedNoStrings, named_strings_chain = get_StringLists(namedFileList, 'library_named')
	unnamedHasStrings, unnamedNoStrings, unnamed_strings_chain = get_StringLists(unnamedFileList, 'library_unnamed')
	
	# Fill out the 'unique_file_strings' and 'unique_lib_strings' portion of the data structure
	named_uniqueStringsChain = unique_StringFinder(named_strings_chain)
	unnamed_uniqueStringsChain = unique_StringFinder(unnamed_strings_chain)
	
	print("Make guess for matches based on strings...")

	# Make some matches and get back any that couldn't be matched yet
	unnamed_stringMatchesChain, still_unknown = string_Matching(named_uniqueStringsChain, unnamed_uniqueStringsChain)

	get_Update(unnamedFileList, unnamed_stringMatchesChain)

	# Make final guesses for files with strings based on unique library strings
	final_String_Guesses, still_unknown2 = unique_StringMatching(still_unknown, named_uniqueStringsChain, unnamed_stringMatchesChain)

	get_Update(unnamedFileList, final_String_Guesses)

	# Get Package name for filtering properly with methods and fields
	# TO-DO method

	# Get field information for NAMED files which DO NOT contain strings
	named_fieldsAndMethods_chainMap = get_FieldsAndMethods(namedNoStrings, 'library_named', 'instantcoffee') # fileList, Directory, packageName

	# Get field information for UNNAMED files which DO NOT contain strings in them and the still unknown files that do contain strings
	unnamedStringsAndMore = unnamedNoStrings + still_unknown2 
	unnamed_fieldsAndMethods_chainMap = get_FieldsAndMethods(unnamedStringsAndMore, 'library_unnamed', 'instantcoffee') # fileList, Directory, packageName

	print('Find matches based on fields and methods...')

	# Make some exact matches with fields and methods and get back any that couldn't be matched
	unnamed_fieldsAndMethods_chain, named_fieldsAndMethods_chain, still_unknown3 = fieldsAndMethods_Matching(named_fieldsAndMethods_chainMap, unnamed_fieldsAndMethods_chainMap)

	get_Update(unnamedFileList, unnamed_fieldsAndMethods_chain)

	print('Make guesses based off fields and methods percent matching...')
	# Try to make reasonable guesses from those that still couldn't be matched
	final_fieldsAndMethods_Guesses, left_unknown = fieldsAndMethods_Guessing(still_unknown3, named_fieldsAndMethods_chain, unnamed_fieldsAndMethods_chain)
	
	get_Update(unnamedFileList, final_fieldsAndMethods_Guesses)

	print('Done')

	#pprint.pprint(left_unknown)

	#for x in final_fieldsAndMethods_Guesses.maps:
	#	if x.get('Filename') != None:
	#		if x.get('guessed_name') == 'unknown':
	#			pprint.pprint(x)
	#	pprint.pprint(x)

	

if __name__ == "__main__":
	main()













