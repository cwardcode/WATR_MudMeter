# Author: Chris Ward
# Date: 04/20/2015
# Version: 4/24/2015
# Description: Reads in data from our CR850 datalogger and stores to a local file
from datetime import datetime

from pycampbellcr1000 import CR1000

from InvalidDateException import InvalidDateException


# ####################################x
# _______Tables on Device ____________#
# Tables that should be on device     #
# TableEachScan                       #
# Table05min                          #
# Table15min                          #
# Table24hr                           #
# ####################################x

# The device we're connecting to,
device = CR1000.from_url('serial:/dev/ttyO0:9600')
# Return all tables from device
tables = device.list_tables()
# Return all files on device
files = device.list_files()

# ###############################################################
# TODO: Remove both calls below, just a simple connection test. #
# ###############################################################

# Print out all tables on device

print('Tables on device:')
print(tables)

# If any files exist, print
print('Files on device:')
print(files)

# TODO: END CONNNECTION TEST #

# Date to begin data collection
start_date = ""

# Date to end data collection
end_date = ""

# Start date, formatted
start_date_form = ""

# End date, formatted
end_date_form = ""

# Ensure date input is valid, loop until valid dates are entered
# TODO: Prompt & specify date format
# TODO: Later, automate for specified interval if needed
while True:
    try:
        start_date = input('Enter a start date to collect data: ')
        end_date = input('Enter an end date to collect data: ')
        print('Formatting date...')
        start_date_form = datetime.strptime(start_date, "%b %d %Y")
        end_date_form = datetime.strptime(end_date, "%b %d %Y")
        # Ensure start date is before end date
        if start_date_form > end_date_form:
            raise InvalidDateException('Invalid date!')
        break
    except ValueError:
        print("Invalid date entered.")
    except InvalidDateException:
        print("End date is before start date!")
# Print data for debugging
print('Input start time: ' + start_date)
print('Input end time: ' + end_date)
print('Formatted start: ' + str(start_date_form))
print('Formatted end: ' + str(end_date_form))

# Now that we have the date, and everything is valid, let's get the data
TableEachScan = device.get_data('TableEachScan', start_date_form, end_date_form)
Table05Min = device.get_data('Table05min', start_date_form, end_date_form)
Table15Min = device.get_data('Table15min', start_date_form, end_date_form)
Table24hr = device.get_data('Table24hr', start_date_form, end_date_form)
TableWipeTimes = device.get_data('WipeTimesTable', start_date_form, end_date_form)

# Open file descriptors for each table
TableEachScan_File = open('TableEachScan.csv', 'w')
Table05Min_File = open('Table05Min.csv', 'w')
Table15Min_File = open('Table15Min.csv', 'w')
Table24hr_File = open('Table24Hr.csv', 'w')
TableWipeTimes_File = open('WipeTimesTable', 'w')

# Write data to files -- should be in root of where script is ran, can output
# to other location if needed. -- maybe a copy in /var/www for website?
TableEachScan_File.read(TableEachScan)
Table05Min_File.read(Table05Min)
Table15Min_File.read(Table15Min)
Table24hr_File.read(Table24hr)
TableWipeTimes_File.read(TableWipeTimes)