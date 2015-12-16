#!/usr/bin/python

##
# Author:      Chris Ward
# Date:        05/26/2015
# Version:     08/26/2015
# Description: An attempt to read in data from our CR850 data logger and stores
#              to files based on table name, while streaming to plot.ly and uploading
#              data to a server
#
# Exit Statuses:
#   1 - Logging device could not be reached on init 
#   2 - GetAddressInfo error occurred trying to reach remote server 
#   3 - Socket error trying to reach remote server 
#   4 - General error occurred and program did not exit correctly, so force exiting 
#   5 - Internet connection error occurred 
##

from datetime import datetime, timedelta
from plotly.graph_objs import Stream, Scatter, Layout, Line, Data, Figure, XAxis, YAxis
from pycampbellcr1000 import CR1000, utils
from pycampbellcr1000.exceptions import NoDeviceException

import os
import platform
import plotly.plotly as py
import plotly.tools as tls
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

# Holds the column name containing the date
datetimeColm = 'Datetime'

# Holds the column names containing data we're monitoring
'''
liveTurbColm = 'TurbNTU2'
liveTurb2Colm = 'TurbNTU3'
liveTurbColm = 'TurbNTU'
liveTurb2Colm = 'TurbNTU2'

NTU2_15_MedColm = 'TurbNTU2_Med'
NTU3_15_MedColm = 'TurbNTU3_Med'

NTU2_24_MedColm = 'TurbNTU2_Med'
NTU3_24_MedColm = 'TurbNTU3_Med'
'''
liveTurbColm = 'TurbNTU'
liveTurb2Colm = 'TurbNTU2'

NTU2_15_MedColm = 'TurbNTU_Med'
NTU3_15_MedColm = 'TurbNTU2_Med'

NTU2_24_MedColm = 'TurbNTU_Med'
NTU3_24_MedColm = 'TurbNTU2_Med'

# Initialize field variables
NTU2_15_Med = 0
NTU3_15_Med = 0
NTU2_24_Med = 0
NTU3_24_Med = 0
# Holds the table that contains the data we're plotting
dataTable = 'TableEachScan'
# The device we're connecting to,
device = CR1000.from_url('serial:/' + location + ":" + port)
# Get all tables from device
tables = device.list_tables()
# Get Streaming Tokens from plot.ly
stream_ids = tls.get_credentials_file()['stream_ids']
# Grab first Token in list
stream_id = stream_ids[0]
# Used to check if header should be used
has_ran = False
# File descriptor for log file
log_file = os.open("logfile.txt", os.O_RDWR | os.O_APPEND | os.O_CREAT)

# Set up traces for plot
dailyTurbidMed = dict(
    x=[],
    y=[],
    type='scatter',
    mode='lines+markers',
    stream=Stream(
        token=stream_ids[1],
        maxpoints=80
    ),
    name="24hr Median Turbidity"
)

liveTurbid = dict(
    x=[],
    y=[],
    type='scatter',
    mode='lines+markers',
    stream=Stream(
        token=stream_ids[2],
        maxpoints=80
    ),
    name="Turbidity Avg Live"
)


fftnMinTurbidMed = dict(
    x=[],
    y=[],
    type='scatter',
    mode='lines+markers',
    stream=Stream(
        token=stream_ids[5],
        maxpoints=80
    ),
    name="15min Median Turbidity"
)

baseNTULevel = dict(
    x=[],
    y=[0],
    type='scatter',
    mode='lines',
    line=Line(
        color='rgb(78,252,119)',
        width=1,
    ),
    stream=Stream(
        token=stream_ids[6],
        maxpoints=80
    ),
    showlegend=False,
    fill='tonexty',
    hoverinfo='none'
)

goodNTULevel = dict(
    x=[],
    y=[10],
    type='scatter',
    mode='lines',
    line=Line(
        color='rgb(78,252,119)',
        width=1,
    ),
    stream=Stream(
        token=stream_ids[0],
        maxpoints=80
    ),
    fill='tonexty',
    name="Normal for trout and fish",
    hoverinfo='none'

)

badNTULevel = dict(
    x=[],
    y=[100],
    type='scatter',
    mode='lines',
    line=Line(
        color='rgb(253,172,79)',
        width=1,
    ),
    stream=Stream(
        token=stream_ids[3],
        maxpoints=80
    ),
    fill='tonexty',
    name="Difficult to treat water",
    hoverinfo='none'

)

uglyNTULevel = dict(
    x=[],
    y=[1000],
    type='scatter',
    mode='lines',
    line=Line(
        color='rgb(253,79,79)',
        width=1,
    ),
    stream=Stream(
        token=stream_ids[4],
        maxpoints=80
    ),
    fill='tonexty',
    name="Water Treatement Not Possible",
    hoverinfo='none'

)
# Set up data sets
plot_data = [fftnMinTurbidMed, dailyTurbidMed, liveTurbid, baseNTULevel, goodNTULevel, badNTULevel, uglyNTULevel]

# Configure the Layout
layout = Layout(
    title='\"Muddyness\" (Turbidity) in Scotts Creek',
    xaxis=XAxis(
        title='Date Time'
    ),
    yaxis=YAxis(
        title='Turbidity(NTU)',
        range=[0,150]
    ),
)

# Create the plot itself
fig = dict(data=plot_data, layout=layout)

# Generate plot.ly URL based on name
unique_url = py.plot(fig, validate=False,filename='WATRDataStream_Dev')

# Holds the connections to the streams
goodTurb_link = py.Stream(stream_ids[0])
dailyTurb_link = py.Stream(stream_ids[1])
liveTurb_link = py.Stream(stream_ids[2])
badTurb_link = py.Stream(stream_ids[3])
uglyTurb_link = py.Stream(stream_ids[4])
fftnMinTurb_link = py.Stream(stream_ids[5])
baseTurb_link = py.Stream(stream_ids[6])

# Holds whether update_plot is currently running
collecting = False

def update_plot(table):
    """
    " update_plot: Updates the plot.ly plot with new data continuously
    " @:argument table - the table from which we're collecting data
    """
    global liveTurbColm
    global liveTurb2Colm
    global fftnDepthColm
    global datetimeColm
    global device
    global log_file
    global fftnMinTurb_link
    global dailyTurb_link
    global liveTurb_link
    global baseTurb_link
    global goodTurb_link
    global badTurb_link
    global uglyTurb_link

    # Start date for data  collection, should be seven seconds in the past (enough time to get new data from sensors)
    sTime = datetime.now() - timedelta(seconds=17)

    # End date for  data collection, should be now, to complete our 15 minute interval
    eTime = datetime.now()

    # Get new data from the logger
    try:
        newData = device.get_data(table, sTime, eTime)
    except NoDeviceException as e:
        output = "Device could not be reached: " + str(e) + "\n"
        print(output)
        os.write(log_file, output)
        emergency_put()
        exit(1)

    output = "Received new data, plotting\n" + str(newData)
    print(output)
    os.write(log_file, output)
    # Plot new Data
    for i in newData:
        x = i[datetimeColm]

        # Average NTU Medians
        MedAvg = ((NTU2_15_Med + NTU3_15_Med) / 2.0)
        Med24Avg = ((NTU2_24_Med + NTU3_24_Med) / 2.0)
        
        # Get live turbidity data
        liveTurb1 = i[liveTurbColm]
        liveTurb2 = i[liveTurb2Colm]
        liveTurbAvg = ((liveTurb1 + liveTurb2) / 2.0)

        # Write new data to plot.ly
        fftnMinTurb_link.write(dict(x=x, y=MedAvg),validate=False)
        dailyTurb_link.write(dict(x=x, y=Med24Avg),validate=False)
        liveTurb_link.write(dict(x=x, y=liveTurbAvg),validate=False)
        baseTurb_link.write(dict(x=x, y=0),validate=False)
        goodTurb_link.write(dict(x=x, y=10),validate=False)
        badTurb_link.write(dict(x=x, y=100),validate=False)
        uglyTurb_link.write(dict(x=x, y=3000),validate=False)

        # Wait 0.80 seconds for new data to be collected
        time.sleep(0.80)

        output = "Plotting new data:\nNUT_15_Med: " + str(MedAvg) + "\nNTU_24_Med: " + str(Med24Avg) + "\nLiveTurb Avg: " + str(liveTurbAvg) + "\n"
        print(output)
        os.write(log_file, output)

        output = "Plotting new data, finished\n"
        print(output)
        os.write(log_file, output)

    return 0


def collect_data(table_name):
    """
    " Function which takes in a table name, gathers its data and exports it as a CSV file for analysis.
    " @:param table_name - name of table to collect data and export
    """
    # 15 minute table data
    global NTU2_15_Med
    global NTU3_15_Med


    # 24 hour table data
    global NTU2_24_Med
    global NTU3_24_Med

    # Start date for data  collection, should be fifteen minutes in the past
    # If table is 24 hours and script hasn't ran, get past 24 hours worth, same for Table15min
    if table_name == "Table24hr" and not has_ran:
        start_date_form = datetime.now() - timedelta(hours=24)
    elif table_name == "Table15min" and not has_ran:
        start_date_form = datetime.now() - timedelta(hours=12)
    else:
        start_date_form = datetime.now() - timedelta(minutes=15)

    # End date for  data collection, should be now, to complete our 15 minute interval
    end_date_form = datetime.now()

    # Check which platform program is running on, if windows treat as binary
    if platform == 'Linux':
        table_file = os.open(table_name + '.csv', os.O_WRONLY | os.O_APPEND | os.O_CREAT)
    else:
        table_file = os.open(table_name + '.csv', os.O_BINARY | os.O_WRONLY | os.O_APPEND | os.O_CREAT)

    # Pull data from table on logger
    table_data = device.get_data(table_name, start_date_form, end_date_form)

    # Get 15 minute medians
    if table_name == "Table15min":
        # Iterate through table data, and set medians
        for i in table_data:
            NTU2_15_Med = i[NTU2_15_MedColm]
            output = "NTU2_Med: " + str(i[NTU2_15_MedColm]) + "\n"
            print(output)
            os.write(log_file, output)

            NTU3_15_Med = i[NTU3_15_MedColm]
            output = "NTU3_Med: " + str(i[NTU3_15_MedColm]) + "\n"
            print(output)
            os.write(log_file, output)

    if table_name == "Table24hr":
        for i in table_data:
            NTU2_24_Med = i[NTU2_24_MedColm]
            output = "NTU2_24_Med: " + str(i[NTU2_24_MedColm]) + "\n"
            print(output)
            os.write(log_file, output)

            NTU3_24_Med = i[NTU3_24_MedColm]
            output = "NTU3_24_Med: " + str(i[NTU3_24_MedColm]) + "\n"
            print(output)
            os.write(log_file, output)
    # Set headers if applicable and convert dictionary to csv file

    if has_ran:
        output = "Script has already ran at least once\n"
        os.write(log_file, output)
        table_csv = utils.dict_to_csv(table_data, ",", header=False)
    else:
        output = "Script has not already ran\n"
        os.write(log_file, output)
        table_csv = utils.dict_to_csv(table_data, ",", header=True)

    output = "Writing file to local storage\n"
    os.write(log_file, output)

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

    output = "files opened\n"
    print(output)
    os.write(log_file, output)

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

    output = "changed to updata\n"
    print(output)
    os.write(log_file, output)

    # Get remote file, and set mode to append
    rem_file = c.file(file_name + '.csv', mode='a', bufsize=1)

    output = "opened tablefile\n"
    print(output)
    os.write(log_file, output)
    # Get remote log file and set mode to overwrite
    #rem_log_file = c.file('logfile.txt', mode='w', bufsize=1)
    #output = "opened logfd\n"
    #print(output)
    #os.write(log_file, output)

    # Write data and clean up
    rem_file.write(loc_file.read())
    #rem_log_file.write(log_file2.read())
    output = "Wrote files to server\n"

    # Flush/close data file streams
    os.write(log_file, output)
    rem_file.flush()
    rem_file.close()
    loc_file.close()

    # Flush/close log file streams
    #rem_log_file.flush()
    #rem_log_file.close()
    #rem_log_file.close()

    output = "File streams closed\n"
    os.write(log_file, output)
    # Remove file after it's uploaded
    os.remove(file_name + '.csv')
    output = "Removed CSV: " + file_name + "\n"
    os.write(log_file, output)

    # Close client
    c.close()

    # Close transport
    t.close()

    return 0


def emergency_put():
    """
    " Uploads Log file to server in event of crash
    """

    output = "********************************\nException detected above at: " + time.strftime("%H:%M:%S") + "!!!! *\n********************************\n"
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


    output = "In get_data, about to set threading timer\n"
    os.write(log_file, output)
    print(output)

    # Set timer to run method again in 15 minutes
    FIFTN_MINUTES_N_SECS = 900
    collect_thread = threading.Timer(FIFTN_MINUTES_N_SECS, get_data)
    collect_thread.start()

    output = "Setting collecting variable to true, should be false: " + str(collecting) + "\n"
    os.write(log_file, output)
    print(output)

    # Set collecting variable to lock access to logger
    collecting = True

    output = "Just set collecting variable to true, should be true now: " + str(collecting) + "\n"
    os.write(log_file, output)
    print(output)

    output = "In get_data, about to pull data from logger\n"
    os.write(log_file, output)
    print(output)

    # Pull data for each table on logger
    for table in tables:
        output = "Inside table iteration, table is: " + str(table) + "\n"
        os.write(log_file, output)
        print(output)
        # Get data
        collect_data(table)

        output = "Inside table iteration, Finished pulling data from table \n"
        os.write(log_file, output)
        print(output)

        # Ensure headers are disabled
    if not has_ran:
        has_ran = True

    output = "In get_data, finished pulling data from logger\n"
    os.write(log_file, output)
    print(output)

    output = "Setting collecting variable to false, should be true: " + str(collecting) + "\n"
    os.write(log_file, output)
    print(output)

    # Finished collecting, unblock and let data upload to plot.ly
    collecting = False

    output = "Just set collecting variable to false, should be false now: " + str(collecting) + "\n"
    os.write(log_file, output)
    print(output)

    return 0


# 15 minutes = 900 seconds
FIFTN_MINUTES_N_SECS = 900

# Holds our thread for collecting data ever N seconds
collect_thread = threading.Timer(FIFTN_MINUTES_N_SECS, get_data)

def checkConnection():
    try:
        response=urllib2.urlopen('http://74.125.224.72',timeout=1)
        output = "received response"
        print(output)
        os.write(log_file, output)
        return True
    except urllib2.URLError as err:
        output = "Error! " + str(err)
        print(output)
        os.write(log_file, output)
        exitStatus = 5
        sys.exit(exitStatus)

def main():
    """
    " Main function of the program, opens stream and allows plot to update.
    """
    global collecting
    global dataTable
    global log_file
    global tables
    global liveTurb_link
    global baseTurb_link
    global goodTurb_link
    global badTurb_link
    global uglyTurb_link
    global fftnMinTurb_link
    global dailyTurb_link

    # Open one connection to plot.ly server for each data point
    fftnMinTurb_link.open()
    dailyTurb_link.open()
    liveTurb_link.open()
    baseTurb_link.open()
    goodTurb_link.open()
    badTurb_link.open()
    uglyTurb_link.open()

    output = "plotly streams opened\n"
    os.write(log_file, output)
    print(output)

    # Collect data every 15 minutes
    get_data()
    output = "Got data!\n"
    os.write(log_file, output)
    # Update plot continuously
    while True:
        if not collecting:
            output = "Checking internet Connection\n"
            print(output)
            os.write(log_file, output)
            checkConnection();
            update_plot(dataTable)
            output = "updated plot\n"
            os.write(log_file, output)
            # Wait 15 seconds before updating
            time.sleep(15)
        else:
            output = "waiting to finish sending data\n"
            print(output)
            os.write(log_file, output)
            # Wait 15 seconds to finish sending data
            time.sleep(15)
    # Close stream to server
    output = "*****\n BROKE OUT OF Main FOR LOOP \n*****\n"
    print(output)
    os.write(log_file, output)

    # Close stream to server -- shouldn't happen, but clean up if necessary
    uglyTurb_link.close()
    badTurb_link.close()
    goodTurb_link.close()
    baseTurb_link.close()
    liveTurb_link.close()
    dailyTurb_link.close()
    fftnMinTurb_link.close()

    output = "Plotly Streams closed\n "
    os.write(log_file, output)
    print(output)

    return 0

# Call main, execute program
try:
    main()
except (KeyboardInterrupt, SystemExit) as kisexit:
    # Cancel thread timer
    collect_thread.cancel()
    # Exit with error status after thread timer is killed
    sys.exit(exitStatus);
