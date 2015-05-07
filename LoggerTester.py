# Author: Chris Ward
# Date: 04/20/2015
# Version: 4/24/2015
# Description: Reads in data from our CR850 data logger and stores to a local file
from datetime import datetime
import os

from pycampbellcr1000 import utils
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

# Holds the device's mapped location
location = "COM1"

# Holds the port on which we're communicating with the device
port = "115200"
print('connecting to logger...')

# The device we're connecting to,
device = CR1000.from_url('serial:/' + location + ":" + port)
print('connected to ' + location + ':' + port)

# ###############################################################
# TODO: Remove both calls below, just a simple connection test. $
# ###############################################################

# Return all files on device
files = device.list_files()
# If any files exist, print
print('Files on device:')
print(files)
# Return all tables from device
tables = device.list_tables()
# Print out all tables on device
print('Tables on device:')
print(tables)


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
        start_date_form = datetime.strptime(str(start_date), "%b %d %Y")
        end_date_form = datetime.strptime(str(end_date), "%b %d %Y")
        # Ensure start date is before end date
        if start_date_form > end_date_form:
            raise InvalidDateException('Invalid date!')
        break
    except ValueError:
        print("Invalid date entered.")
    except InvalidDateException:
        print("End date is before start date!")

"""
" function which takes in a table name, gathers its data and exports it as a CSV file for analysis.
" @:param table_name - name of table to collect data and export
"""


def scantable(table_name):
    table_file = os.open(table_name + '.csv', os.O_WRONLY | os.O_APPEND | os.O_CREAT)
    table = device.get_data(table_name, start_date_form, end_date_form)
    table_csv = utils.dict_to_csv(table, ",", header=True)
    os.write(table_file, table_csv.encode('UTF-8'))


"""
" Call tables to scan.
"""
# TODO: Make this automatic from get_tables()

scantable('TableEachScan')
scantable('Table05Min')
scantable('Table15Min')
scantable('Table24Hr')
