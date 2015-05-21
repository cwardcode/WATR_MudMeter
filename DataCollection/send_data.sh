#!/bin/bash
##
# Author: Chris Ward <chris@cwardcode.com>
# Name: send_data.sh
# Desc: A script that appends data to files on a server, ensures data preservation
#       with the use of lock files.
# Exit values:
# 0 - Successfully exited
# 1 - The script is already executing
# 2 - The data isn't finished updating yet
##

# Check to see if script is already running
if [ -f ".scriptlock" ]
then
    echo "script is already running!"
    exit 1
else
    $(touch .scriptlock)
    echo "scriptlock created"
fi

    
# Ensure data isn't currently being collected
if [ -f ".datalock" ]
then
    echo "The data is locked, can't touch yet"
    exit 2
else
	# Loop through files and upload changes
	for csv in /root/*.csv
		do
			# If file size > 0, append changes on server
			if [ -s $csv ]
			then
				# Get current file name
				filename=$(basename $csv)
				# Append file
				cat $csv | ssh cdward4@trantracker.com "cat >> ./updata/$filename"
				echo "Files uploaded, zeroing out local data"
				$(> $csv)
			else
				echo "file is empty! nothing to do"
			fi
		done
	fi
# Remove the lock since the script is exiting
echo "Removing lock file and exiting"
rm ".scriptlock"

# Exit successfully
exit 0
