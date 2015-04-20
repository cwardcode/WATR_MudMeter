__author__ = 'Chris Ward'

from datetime import datetime

from pycampbellcr1000 import CR1000

from InvalidDateException import InvalidDateException

# ####################################x
# ____________________________________#
# Tables that should be on device     #
# TableEachScan                       #
# Table05min                          #
# Table15min                          #
# Table24hr                           #
# ####################################x

device = CR1000.from_url('serial:/dev/ttyO0:115200')
# Return all tables from device
tables = device.list_tables()
# Return all files on device
files = device.list_files()

print('Tables on device:')
print(tables)

print('Files on device:')
print(files)

start_date = ""
end_date = ""
start_date_form = ""
end_date_form = ""

# ensure date input is valid
while True:
    try:
        start_date = input('Enter a start date to collect data: ')
        end_date = input('Enter an end date to collect data: ')
        print('Formatting date...')
        start_date_form = datetime.strptime(start_date, "%b %d %Y")
        end_date_form = datetime.strptime(end_date, "%b %d %Y")
        if start_date_form > end_date_form:
            raise InvalidDateException('Invalid date!')
        break
    except ValueError:
        print("Invalid date entered.")
    except InvalidDateException:
        print("End date is before start date!")

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
# Open file descriptors
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
