import os, subprocess, sys, argparse, re, collections, pprint

# Methods 

###########################
# Get a list of file names #
###########################
def getFileNames(aDirectory):
	a = subprocess.Popen('ls %s' % aDirectory, stdout=subprocess.PIPE, shell=True)
	output, error = a.communicate()
	output = output.decode('utf-8')

	# Check for special characters in the names
	check = re.compile('[@!#$%^&*()<>?/\|}{~:]')
	if(check.search(output) == None):
		print("Creating file name list..")
		file_list = output.splitlines()
		return file_list
	else:
		print("ERROR: File names cannot contain special characters:")
		file_error_list = output.splitlines()

		# Print out what the offending files are
		for x in file_error_list:
			if(check.search(x) != None):
				print(x)
		print("exiting..")
		sys.exit()	

	# TO-DO
	# Check that all given filenames are unique!

	# TO-DO
	# Method for renaming files with special characters since the dollar sign is such a common occurence with pro-guard
	# linux command: mv oldfile.txt newfile.txt

###########################
# For getting an update on 
# number of files guessed
###########################
def getUpdate(unnamed_file_list, chain_map):
	total_files = len(unnamed_file_list)
	guesses_count = 0

	for x in chain_map.maps:
		if x.get('Filename') != None:
			if x.get('guessed_name') != 'unknown':
				guesses_count += 1

	print(str(guesses_count) + ' / ' + str(total_files) + ' files guessed')

###########################
# Create initial dictionaries
# and fill in file string
# info for each library
###########################
def getStrings(file_list, directory):
	has_strings = []
	no_strings = []
	strings_list = []
	index = 0
	chain_map = collections.ChainMap()

	for x in file_list:
		tmp_directory = directory + "/" + x
		b = subprocess.Popen('grep -a "const-string" %s' % tmp_directory, stdout=subprocess.PIPE, shell=True)
		strings, error_temp = b.communicate()

		# TO-DO: add error check here
		strings = strings.decode('utf-8')
	
		# If no strings in file store results in list
		#if not strings:
		#	no_strings.append(x)
		#else:
		#	has_strings.append(x)
		if strings:
			# Filter out strings
			strings_list = re.findall('"([^"]*)"', strings) 

		# Create a new dictionary element for every file 
		# regardless if there are strings or not
		tmp_dict = {
		"Filename": x,
		"no_of_strings": len(strings_list),
		"new_name" : "unknown",
		"guessed_name" : "unknown",
		"strings": strings_list,
		"unique_file_strings" : [],
		"unique_lib_strings" : [],
		"no_of_fields" : 0,
		"fields" : [],
		"no_of_methods" : 0,
		"methods" : []
		}
	
		chain_map = chain_map.new_child(tmp_dict)

		# Reset values
		tmp_directory = ""
		strings_list = []
	
	return chain_map

###########################
# Find which files have strings
# unique to the entire library
###########################

# TO-DO Make this method function better 
# now that we are passing through a single chain map (file_chain)
def getUniqueStrings(file_chain):
	unique_file_strings = []

	# For each unnamed file extract the strings unique to that file
	for x in file_chain.maps:
		if x.get('Filename') != None:
			file_string_list = x.get('strings')
			occurences_unnamed = collections.Counter(file_string_list) 

			# Check the occurences of the string in the file, 
			# if it is only once then add it to the list of unique file strings
			for y in occurences_unnamed:
				if occurences_unnamed[y] == 1:
					unique_file_strings.append(x)
					#z = x.get('unique_file_strings')
					#z.append(y) # append the string to the unique file strings list

					#if y not in total_unique_fStrings:
					#	total_unique_fStrings.append(y) # append the string to the total unique file strings list
					#	z = x.get('unique_lib_strings')
					#	z.append(y)

	return file_chain

###########################
# Try to find file matches 
# based off of string matches
###########################
def stringMatching(named_chain, unnamed_chain):
	still_unknown_chain = collections.ChainMap()

	for uFile in unnamed_chain.maps:
		if uFile.get('Filename') != None:
			for nFile in named_chain.maps:
				if uFile.get('no_of_strings') > 0 and uFile.get('no_of_strings') == nFile.get('no_of_strings'):
					uFile_strings = uFile.get('strings')
					nFile_strings = nFile.get('strings')

					# if strings array of x is the same as string array of guess z
					if set(uFile_strings) == set(nFile_strings):
						#print('Guess is that ' + x.get('Filename') + " is " + z.get('Filename'))
						uFile.update(guessed_name = nFile.get('Filename'))
						break

					# TO-DO should change this to do percentage comparison probably? Not sure why 
					# I didn't do that first. Will investigate further.
					#if uFile.get('no_of_strings') >= 2:
					#	inList = 0
					#	notInList = 0

						# If there are more strings that match then that don't match, make a guess.
					#	for v in tmpX: # for each string in the file x string list
					#		if v in tmpY: # if that string is in the guess z file string list
					#			inList+=1
					#		else:
					#			notInList+=1
					#	if inList > notInList:
					#		x.update(guessed_name = y.get('Filename'))

			if uFile.get('guessed_name') == 'unknown':
				still_unknown_chain = still_unknown_chain.new_child(uFile)
				
	return unnamed_chain, still_unknown_chain

###########################
# Given a list of unknown files 
# with unique library strings
# try and find matches
###########################
def uniqueStringMatching(still_unknown, named_strings_chain, unnamed_strings_chain):
	still_unknown_list = []
	for sFile in still_unknown.maps:
		if sFile.get('Filename') != None and sFile.get('unique_lib_strings'):
			sList = sFile.get('unique_lib_strings')

			# Iterate over the named files to find a match
			for nFile in named_strings_chain.maps:
				if nFile.get('Filename') != None and nFile.get('unique_lib_strings'):
					nList = nFile.get('unique_lib_strings')

					# Generate a percentage value of how similar the two lists are
					evaluate = len(set(sList) & set(nList)) / float(len(set(sList) | set(nList))) * 100

					# Iterate over the unnamed files and assign 
					# guesses or matches based on how close the matches are
					# for the unique library strings list
					for uFile in unnamed_strings_chain.maps:
						if uFile.get('Filename') == sFile.get('Filename'):
							if evaluate == 100.0:
								uFile.update(guessed_name = nFile.get('Filename')) # if we have a new name then we have a guessed name
								uFile.update(new_name = nFile.get('Filename'))
							elif evaluate > 50.0:
								uFile.update(guessed_name = nFile.get('Filename'))
							else:
								continue

			# If there are still no guesses for the file, put it
			# in a collections to return and pass to the fields and 
			# methods matching/guesses functions
			if sFile.get('guessed_name') == 'unknown':
				still_unknown_list.append(sFile.get('Filename'))
						
	return unnamed_strings_chain, still_unknown_list

###########################
# Get fields and methods attributes 
# for files in both libraries
###########################		
def getFieldsAndMethods(file_chain, directory, package_name):
	fields_methods_chain = collections.ChainMap()
	fields_list = []
	methods_list = []
	methods_re = re.compile('L' + package_name + '/[a-z_]*')

	for x in file_chain.maps:
		if x.get('Filename') != None:
			tmp_directory = directory + "/" + x.get('Filename')

			# Get fields
			b = subprocess.Popen('grep -a ".field " %s' % tmp_directory, stdout=subprocess.PIPE, shell=True)
			fields, error = b.communicate()
			fields = fields.decode('utf-8')

			# Extract fields with regex
			if fields:
				# Filter out field names (for package fields they will be differently named)
				tmp_fields_list = re.findall('((\\b)([a-zA-Z0-9_]+):(.)*$)', fields, flags=re.M)

				# Rename package object fields to generic name
				# since theres no point comparing them
				for y in tmp_fields_list:
					if package_name in y[0]:
						fields_list.append(package_name)
					else:
						fields_list.append(y[0])

				# Update fields attribute
				x.update(fields = fields_list)
				x.update(no_of_fields = len(fields_list))
				
			# Get methods
			# Do a grep of the methods in the file
			c = subprocess.Popen('grep -a ".method " %s' % tmp_directory, stdout=subprocess.PIPE, shell=True)
			methods, error2 = c.communicate()
			methods = methods.decode('utf-8')
	
			# Extract methods with regex
			if methods:
				tmp_methods_list = re.findall('((\\b)([a-zA-Z0-9_]+)\((.)*$|constructor.*$)', methods, flags=re.M)
			
				# A bit trickier, use regex to replace "Linstantcoffee/x" occurences with just "instantcoffee"
				# while maintaining everything else so that we don't lose the form of the method signature
				for y in tmp_methods_list:
					if package_name in y[0]:
						methods_list.append(methods_re.sub(package_name, y[0]))
					else:
						methods_list.append(y[0])

				x.update(methods = methods_list)
				x.update(no_of_methods = len(methods_list))
			# Create a dictionary entry regardless of if ohhhhh wfyuc
			#tmp_dict = {
			#"Filename": x,
			#"no_of_fields": len(fields_list),
			#"fields" : fields_list,
			#"no_of_methods": len(methods_list),
			#"methods" : methods_list,
			#"new_name" : "unknown",
			#"guessed_name" : "unknown"
			#}

			#fields_methods_chain = fields_methods_chain.new_child(tmp_dict)

			# Reset values
			tmp_directory = ""
			fields_list = []
			methods_list = []
	
		return file_chain

# Take in dicts of information on fields and methods and do comparisons to try and make matches
# (similar method to the string matching method)
def fieldsAndMethodsMatching(named_fieldsAndMethods_chainMap, unnamed_fieldsAndMethods_chainMap):
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
def fieldsAndMethodsGuessing(still_unknown3, named_fieldsAndMethods_chain, unnamed_fieldsAndMethods_chain):
	left_unknown = collections.ChainMap()
	evaluate_fields = 0.0
	evaluate_methods = 0.0

	for sFile in still_unknown3.maps:
		if sFile.get('Filename') != None:

			# Don't try to make estimates with files that have no fields 
			# or no methods because it won't be a good enough guess
			if sFile.get('no_of_fields') != 0 and sFile.get('no_of_methods') != 0:
				# Get the files fields and methods list
				u2_fieldsList = sFile.get('fields')
				u2_methodsList = sFile.get('methods')

				# Iterate over the named files to find a match
				for nFile in named_fieldsAndMethods_chain.maps:
					if nFile.get('Filename') != None and nFile.get('guessed_name') == 'unknown': # no point comparing to files that already have matches
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
					#	print('Percentage simliarity of fields in file ' + sFile.get('Filename') + ' and ' + nFile.get('Filename') + ': ' + str(evaluate_fields))

					#if evaluate_methods > 0.0:
					#	print('Percentage simliarity of methods in file ' + sFile.get('Filename') + ' and ' + nFile.get('Filename') + ': ' + str(evaluate_methods))

					# Iterate over the unnamed files and assign 
					# guesses or matches based on how close the matches are
					# for the methods and fields lists
						for uFile in unnamed_fieldsAndMethods_chain.maps:
							if uFile.get('Filename') == sFile.get('Filename'): # find where in the unnamed list is the unknown file we're evaluating
								if evaluate_methods > 49.0 and evaluate_fields > 49.0:
									# Don't overwrite guesses we already made
									if uFile.get('guessed_name') == 'unknown':
										#print('making a guess')
										uFile.update(guessed_name = nFile.get('Filename'))
										break # stop looking, since we were just searching for the matching file to either update the guessed_name value or not
									#else:
										#print('already made a guess for ' + uFile.get('Filename'))
							else:
									#if evaluate_fields > 0.0 or evaluate_methods > 0.0:
									#	print('Not sure who ' + sFile.get('Filename') + ' is.')
									#	print('Percentage simliarity of fields in file ' + sFile.get('Filename') + ' and ' + nFile.get('Filename') + ': ' + str(evaluate_fields))
									#	print('Percentage simliarity of methods in file ' + sFile.get('Filename') + ' and ' + nFile.get('Filename') + ': ' + str(evaluate_methods))
								continue # keep searching for the matching file

					#left_unknown = left_unknown.new_child(File)
						
	return unnamed_fieldsAndMethods_chain, left_unknown


def main():
	#aDirectory = ""
	#parser = argparse.ArgumentParser(description='A program for renaming similar APKs')
	
	# Get a list of each libraries file names
	named_file_list = getFileNames('library_named')
	unnamed_file_list = getFileNames('library_unnamed')
	
	# Create a chainmap (a dictionary of dictionaries) and fill in the 
	# strings attribute of each dictionary for each file in the 
	# named library of files
	named_chain = getStrings(named_file_list, 'library_named') # returns 2 lists and a chain map

	# Do the same for the unnamed library of files
	unnamed_chain = getStrings(unnamed_file_list, 'library_unnamed') # returns 2 lists and a chain map
	
	pprint.pprint(unnamed_chain)

	# Fill out the 'unique_file_strings' and 'unique_lib_strings' portion of the dictionaries for each library
	#named_chain = getUniqueStrings(named_chain)
	#unnamed_chain = getUniqueStrings(unnamed_chain)
	
	#print("Make guess for matches based on strings...")

	# Make some matches and get back any that couldn't be matched yet
	#unnamed_chain, still_unknown_chain = \
	#stringMatching(named_chain, unnamed_chain)

	#getUpdate(unnamed_file_list, unnamed_chain)

	

	# Make final guesses for files with strings based on unique library strings
	#unnamed_chain, still_unknown_list = \
	#uniqueStringMatching(still_unknown_chain, named_chain, unnamed_chain)

	#getUpdate(unnamed_file_list, unnamed_chain)

	# Get Package name for filtering properly with methods and fields
	# TO-DO method

	# Get field information for NAMED files which DO NOT contain strings
	#named_fields_methods_chain = getFieldsAndMethods(named_chain, 'library_named', 'instantcoffee') # fileList, Directory, packageName

	# Get field information for UNNAMED files which DO NOT contain strings in them and the still unknown files that do contain strings
	#unnamed_list = unnamed_no_strings + still_unknown_list
	#unnamed_fields_methods_chain = getFieldsAndMethods(unnamed_chain, 'library_unnamed', 'instantcoffee') # fileList, Directory, packageName

	#print('Find matches based on fields and methods...')

	# Make some exact matches with fields and methods and get back any that couldn't be matched
	#unnamed_fields_methods_chain, named_fields_methods_chain, still_unknown3 = fieldsAndMethodsMatching(named_fields_methods_chain, unnamed_fields_methods_chain)

	#getUpdate(unnamed_file_list, unnamed_fields_methods_chain)

	#print('Make guesses based off fields and methods percent matching...')
	# Try to make reasonable guesses from those that still couldn't be matched
	#final_fields_methods_chain, left_unknown = fieldsAndMethodsGuessing(still_unknown3, named_fields_methods_chain, unnamed_fields_methods_chain)
	
	#getUpdate(unnamed_file_list, final_fields_methods_chain)

	#print('Done')

	#pprint.pprint(unnamed_fields_methods_chain)

	#for x in final_fieldsAndMethods_Guesses.maps:
	#	if x.get('Filename') != None:
	#		if x.get('guessed_name') == 'unknown':
	#			pprint.pprint(x)
	#	pprint.pprint(x)

	

if __name__ == "__main__":
	main()













