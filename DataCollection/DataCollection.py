#!/usr/bin/python

##
# Author:      Chris Ward
# Date:        05/26/2015
# Version:     12/14/2015
# Description: An attempt to read in data from our CR850 data logger and store
#              to files based on table name, then upload data to a server
#
# Exit Statuses:
#   1 - Logging device could not be reached on init 
#   2 - GetAddressInfo error occurred trying to reach remote server 
#   3 - Socket error trying to reach remote server 
#   4 - General error occurred and program did not exit correctly, so force exiting 
##

from datetime import datetime, timedelta
from pycampbellcr1000 import CR1000, utils
from pycampbellcr1000.exceptions import NoDeviceException

import os
import platform
import paramiko
import socket
import sys
import threading
import time
import urllib2


# Holds exit status
exitStatus = 0
# Check system platform, if windows, we need to open files in binary mode
platform = platform.system()
# Holds the device's mapped location
if platform == 'Linux':
    location = "dev/ttyAMA0"
elif platform == 'Windows':
    location = "COM1"
else:
    location = "COM1"
# Holds the port on which we're communicating with the device
port = "115200"

# The device we're connecting to,
device = CR1000.from_url('serial:/' + location + ":" + port)

# Get all tables from device
tables = device.list_tables()

# Used to check if header should be used
has_ran = False

# File descriptor for log file
log_file = os.open("logfile.txt", os.O_RDWR | os.O_APPEND | os.O_CREAT)

# Holds whether update_plot is currently running
collecting = False

def collect_data(table_name):
    """
    " Function which takes in a table name, gathers its data and exports it as a CSV file for analysis.
    " @:param table_name - name of table to collect data and export
    """

    # Start date for data  collection, should be fifteen minutes in the past
    # If table is 24 hours and script hasn't ran, get past 24 hours worth, same for Table15min
    if table_name == "Table24hr" and not has_ran:
        start_date_form = datetime.now() - timedelta(hours=24)
    elif table_name == "Table15min" and not has_ran:
        start_date_form = datetime.now() - timedelta(hours=12)
    else:
        start_date_form = datetime.now() - timedelta(hours=1)

    # End date for  data collection, should be now, to complete our 15 minute interval
    end_date_form = datetime.now()

    # Check which platform program is running on, if windows treat as binary
    if platform == 'Linux':
        table_file = os.open(table_name + '.csv', os.O_WRONLY | os.O_APPEND | os.O_CREAT)
    else:
        table_file = os.open(table_name + '.csv', os.O_BINARY | os.O_WRONLY | os.O_APPEND | os.O_CREAT)

    # Pull data from table on logger
    table_data = device.get_data(table_name, start_date_form, end_date_form)

    # Set headers if applicable and convert dictionary to csv file
    if has_ran:
        table_csv = utils.dict_to_csv(table_data, ",", header=False)
    else:
        table_csv = utils.dict_to_csv(table_data, ",", header=True)


    # Write table file to system
    os.write(table_file, table_csv.encode('UTF-8'))

    # Close file descriptor
    os.close(table_file)

    output = "uploading file to server\n"
    os.write(log_file, output)

    # Upload/Append data to server
    put_data(table_name)

    output = "Wrote file to server\n"
    os.write(log_file, output)

    return 0


def put_data(file_name):
    """
    " Uploads a new data file to remote server via ssh
    """
    # Create file descriptor for table file
    loc_file = open(file_name + '.csv', 'rw')

    # Create file descriptor for log file
    #log_file2 = open('logfile.txt', 'r')


    # Holds private key used to connect to server
    key = paramiko.RSAKey.from_private_key_file('keyp1.pem')

    # Try establishing connection to server
    try:
        # Holds Transport socket
        t = paramiko.Transport(('aws.cwardcode.com', 22))
        # Attempt to connect with key
        t.connect(username='ubuntu', pkey=key)
        # Create sftp session
        c = paramiko.SFTPClient.from_transport(t)

    except socket.gaierror as e:
        # getAddrInfo error occured, so let's collect data and exit
        output = "GetAddressInfo error occurred: " + str(e)
        print(output)
        os.write(log_file, output)
        emergency_put()
        exitStatus = 2
        sys.exit(exitStatus)

    except socket.error as e:
        # Socket error occured, so let's collect data and exit
        output = "Connection error occurred: " + str(e)
        print(output)
        os.write(log_file, output)
        emergency_put()
        exitStatus = 3
        sys.exit(exitStatus)

    # Change into where data is stored
    c.chdir('updata')

    # Get remote file, and set mode to append
    rem_file = c.file(file_name + '.csv', mode='a', bufsize=1)

    # Write data and clean up
    rem_file.write(loc_file.read())
    output = "Wrote files to server\n"
    print(output)

    # Flush/close data file streams
    os.write(log_file, output)
    rem_file.flush()
    rem_file.close()
    loc_file.close()

    # Remove file after it's uploaded
    os.remove(file_name + '.csv')

    # Close client
    c.close()

    # Close transport
    t.close()

    return 0


def emergency_put():
    """
    " Uploads Log file to server in event of crash
    """

    output = "********************************\nException detected above at: " \\ 
                          + time.strftime("%H:%M:%S") + "!!!! *\n********************************\n"
    os.write(log_file, output)
    log_file2 = open('logfile.txt', 'r')
    output = "files opened\n"
    print(output)
    os.write(log_file, output)
    # Holds private key to connect to server
    key = paramiko.RSAKey.from_private_key_file('keyp1.pem')
    # Holds Transport socket
    t = paramiko.Transport(('aws.cwardcode.com', 22))
    # Attempt to connect with key
    t.connect(username='ubuntu', pkey=key)
    # Create sftp session
    c = paramiko.SFTPClient.from_transport(t)
    # Change into where data is stored
    c.chdir('updata')
    # Get remote file, and set mode to append
    rem_log_file = c.file('logfile.txt', mode='w', bufsize=1)
    # Write data and clean up
    rem_log_file.write(log_file2.read())
    # Flush/close log file streams
    rem_log_file.flush()
    rem_log_file.close()
    rem_log_file.close()

    return 0


def get_data():
    """
    " Collects data from the logger every 15 minutes and stores in file to send
    """
    global collect_thread
    global collecting
    global has_ran
    global tables

    if collecting is True:
        output = "Error occurred, exiting\n"
        os.write(log_file, output)
        print(output)
        collect_thread.exit()
        exitStatus = 4
        sys.exit(exitStatus)


    # Set timer to run method again in 60 minutes
    SIXTY_MINUTES_N_SECS = 3600
    collect_thread = threading.Timer(SIXTY_MINUTES_N_SECS, get_data)
    collect_thread.start()

    # Set collecting variable to lock access to logger
    collecting = True

    # Pull data for each table on logger
    for table in tables:
        # Get data
        collect_data(table)
    # Ensure headers are disabled
    if not has_ran:
        has_ran = True

    output = "Finished pulling data from logger\n"
    os.write(log_file, output)
    print(output)

    # Finished collecting, unblock and let data upload to plot.ly
    collecting = False

    return 0


# 60 minutes = 3060 seconds
SIXTY_MINUTES_N_SECS = 3600

# Holds our thread for collecting data ever N seconds
collect_thread = threading.Timer(SIXTY_MINUTES_N_SECS, get_data)

def main():
    """
    " Main function of the program, collects initial data, then sets thread timer to update
    " every hour
    """
    # Collect data every 15 minutes
    get_data()

    return 0

# Call main, execute program
try:
    main()
except (KeyboardInterrupt, SystemExit) as kisexit:
    # Cancel thread timer
    collect_thread.cancel()
    # Exit with error status after thread timer is killed
    sys.exit(exitStatus);
