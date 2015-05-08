# Author: Chris Ward
# Date: 04/20/2015
# Version: 5/08/2015
# Description: Reads in data from our CR850 data logger and stores to files based on table name.

from datetime import datetime
from InvalidDateException import InvalidDateException
from pycampbellcr1000 import CR1000
from pycampbellcr1000 import utils
import platform
import os


# Check system platform, if windows, we need to open files in binary mode
platform = platform.system()
print("platform is: " + str(platform))

# Holds the device's mapped location
if platform == 'Linux':
    location = "/dev/ttyO0"
elif platform == 'Windows':
    location = "COM1"
else:
    location = "COM1"

# Holds the port on which we're communicating with the device
port = "115200"
print('connecting to logger...')

# The device we're connecting to,
device = CR1000.from_url('serial:/' + location + ":" + port)
print('connected to ' + location + ':' + port)

# Return all tables from device
tables = device.list_tables()
# Print out all tables on device
print('Tables on device: ')
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
# TODO: Later, automate for specified interval if needed
while True:
    try:
        start_date = raw_input('Enter a start date to collect data: ')
        end_date = raw_input('Enter an end date to collect data: ')
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

"""
" function which takes in a table name, gathers its data and exports it as a CSV file for analysis.
" @:param table_name - name of table to collect data and export
"""


def collect_data(table_name):
    exists = False
    if os.path.exists(table_name + '.csv'):
        exists = True
    if platform == 'Linux':
        table_file = os.open(table_name + '.csv', os.O_WRONLY | os.O_APPEND | os.O_CREAT)
    else:
        table_file = os.open(table_name + '.csv', os.O_BINARY | os.O_WRONLY | os.O_APPEND | os.O_CREAT)
    table_data = device.get_data(table_name, start_date_form, end_date_form)

    if exists:
        table_csv = utils.dict_to_csv(table_data, ",", header=False)
    else:
        table_csv = utils.dict_to_csv(table_data, ",", header=True)

    os.write(table_file, table_csv.encode('UTF-8'))
    os.close(table_file)

"""
" Iterate through tables list, and collect data from each
"""

for table in tables:
    collect_data(table)