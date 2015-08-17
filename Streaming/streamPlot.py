#!/usr/bin/python
##
# Author:      Chris Ward
# Date:        05/26/2015
# Version:     07/26/2015
# Description: An attempt to read in data from our CR850 data logger and stores
#              to files based on table name, while streaming to plot.ly and uploading
#              data to a server
##

from datetime import datetime, timedelta
from plotly.graph_objs import Stream, Scatter, Layout, Data, Figure, XAxis, YAxis, Legend

from pycampbellcr1000 import CR1000, utils
from pycampbellcr1000.exceptions import NoDeviceException
import os
import platform
import plotly.plotly as py
import plotly.tools as tls
import paramiko
import threading
import time

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
# Holds the column names containing data we're monitoring
dataColm = 'TurbNTU'
dataColm2 = 'TurbNTU2'
dataColm3 = 'TurbNTU3'
tempColm = 'AquiTemp'
depthColm2 = 'DepthFT2'
NTU2_Med = "0"
NTU3_Med = "0"
# Holds the table that contains the data we're plotting
dataTable = 'TableEachScan'
# Holds the column name containing the date
dateColm = 'Datetime'
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

# Set up our traces
turbidity = Scatter(
    x=[],
    y=[],
    mode='lines+markers',
    stream=Stream(
        token=stream_id,
        maxpoints=80
    ),
    name="Ana 1 (NTU)"
)

turbidity2 = Scatter(
    x=[],
    y=[],
    mode='lines+markers',
    stream=Stream(
        token=stream_ids[1],
        maxpoints=80
    ),
    name="Ana 2 (NTU)"
)

turbidity3 = Scatter(
    x=[],
    y=[],
    mode='lines+markers',
    stream=Stream(
        token=stream_ids[2],
        maxpoints=80
    ),
    name="AquiTurbo (NTU)"
)


temperature = Scatter(
    x=[],
    y=[],
    mode='lines+markers',
    stream=Stream(
        token=stream_ids[3],
        maxpoints=80
    ),
    name="AquiTemp (Deg C)"
)

depth = Scatter(
    x=[],
    y=[],
    mode='lines+markers',
    stream=Stream(
        token=stream_ids[4],
        maxpoints=80
    ),
    name="Depth (ft)"
)

median = Scatter(
    x=[],
    y=[],
    mode='lines+markers',
    stream=Stream(
        token=stream_ids[5],
        maxpoints=80
    ),
    name="Median Turbidity (NTU)"
)

# Set up data sets
plot_data = Data([turbidity, turbidity2, turbidity3, temperature, depth, median])

# Configure the Layout
layout = Layout(
    title='NTU Over Time',
    xaxis=XAxis(
        title='Date Time'
    ),
    yaxis=YAxis(
        title='Turbidity(NTU)'
    )
)

# Create the plot itself
fig = Figure(data=plot_data, layout=layout)
# Generate plot.ly URL based on name
unique_url = py.plot(fig, filename='WATRDataStream_With_Median')
# Holds the connections to the streams
stream_link = py.Stream(stream_id)
turb2_link = py.Stream(stream_ids[1])
turb3_link = py.Stream(stream_ids[2])
temp_link = py.Stream(stream_ids[3])
depth2_link = py.Stream(stream_ids[4])
median_link = py.Stream(stream_ids[5])

# Holds whether update_plot is currently running
collecting = False


def update_plot(table):
    """
    " update_plot: Updates the plot.ly plot with new data continuously
    " @:argument table - the table from which we're collecting data
    """
    global dataColm
    global dataColm2
    global dataColm3
    global depthColm2
    global dateColm
    global device
    global log_file
    global stream_link
    global turb2_link
    global turb3_link
    global temp_link
    global depth2_link
    global median_link

    # Start date for data  collection, should be fifteen minutes in the past
    sTime = datetime.now() - timedelta(seconds=7)

    # End date for  data collection, should be now, to complete our 15 minute interval
    eTime = datetime.now()

    # Get new data from the logger
    newData = device.get_data(table, sTime, eTime)

    output = "Received new data, plotting\n"
    print(output)
    os.write(log_file, output)
    for i in newData:
        x = i[dateColm]

        #Average NTU Medians
        MedAvg = ((NTU2_Med + NTU3_Med) / 2)

        stream_link.write(dict(x=x, y=i[dataColm]))
        turb2_link.write(dict(x=x, y=i[dataColm2]))
        turb3_link.write(dict(x=x, y=i[dataColm3]))
        temp_link.write(dict(x=x, y=i[tempColm]))
        depth2_link.write(dict(x=x, y=i[depthColm2]))
        median_link.write(dict(x=x, y=MedAvg))
        time.sleep(0.80)

        output = "Plotting new data:\nNTU1: " + str(i[dataColm]) + "\nNTU2: " + str(i[dataColm2]) + "\nNTU3: " + str(i[dataColm3]) + "\nTemp: " + str(i[tempColm]) + "\nDepth: " + str(i[depthColm2]) + "\nMed: " + str(MedAvg) + "\n"
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
    global has_ran
    global NTU2_Med
    global NTU3_Med
    # Start date for data  collection, should be fifteen minutes in the past
    start_date_form = datetime.now() - timedelta(minutes=15)

    # End date for  data collection, should be now, to complete our 15 minute interval
    end_date_form = datetime.now()

    if platform == 'Linux':
        table_file = os.open(table_name + '.csv', os.O_WRONLY | os.O_APPEND | os.O_CREAT)
    else:
        table_file = os.open(table_name + '.csv', os.O_BINARY | os.O_WRONLY | os.O_APPEND | os.O_CREAT)

    #Pull data from table on logger
    table_data = device.get_data(table_name, start_date_form, end_date_form)
    if table_name == "Table15min":
        for i in table_data:
            NTU2_Med = i['TurbNTU2_Med']
            output = "NTU2_Med: " + str(i['TurbNTU2_Med']) + "\n"
            print(output)
            os.write(log_file, output)
            NTU3_Med = i['TurbNTU3_Med']
            output = "NTU3_Med: " + str(i['TurbNTU3_Med']) + "\n"
            print(output)
            os.write(log_file, output)
    # Set headers and convert dictionary to csv file
    if has_ran:
        output = "Script has already ran at least once\n"
        os.write(log_file, output)
        table_csv = utils.dict_to_csv(table_data, ",", header=False)
    else:
        output = "Script has not already ran\n"
        os.write(log_file, output)
        table_csv = utils.dict_to_csv(table_data, ",", header=True)
        has_ran = True

    output = "Writing file to local storage\n"
    os.write(log_file, output)
    os.write(table_file, table_csv.encode('UTF-8'))
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
    " Uploads new data to server via ssh
    """

    loc_file = open(file_name + '.csv', 'rw')
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
    output = "changed to updata\n"
    print(output)
    os.write(log_file, output)
    # Get remote file, and set mode to append
    rem_file = c.file(file_name + '.csv', mode='a', bufsize=1)
    output = "opened tablefile\n"
    print(output)
    os.write(log_file, output)
    rem_log_file = c.file('logfile.txt', mode='w', bufsize=1)
    output = "opened logfd\n"
    print(output)
    os.write(log_file, output)
    # Write data and clean up
    rem_file.write(loc_file.read())
    rem_log_file.write(log_file2.read())
    output = "Wrote files to server\n"
    os.write(log_file, output)
    #Flush/close data file streams
    rem_file.flush()
    rem_file.close()
    loc_file.close()
    #Flush/close log file streams
    rem_log_file.flush()
    rem_log_file.close()
    rem_log_file.close()
    output = "File streams closed\n"
    os.write(log_file, output)
    os.remove(file_name + '.csv')
    output = "Removed CSV: " + file_name + "\n"
    os.write(log_file, output)
    # Close client connection
    c.close()
    # Close transport socket
    t.close()

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
    #Flush/close log file streams
    rem_log_file.flush()
    rem_log_file.close()
    rem_log_file.close()


def get_data():
    """
    " Collects data from the logger every 15 minutes and stores in file to send
    """
    global collecting
    global tables

    output = "Setting collecting variable to true, should be false: " + str(collecting) + "\n"
    os.write(log_file, output)
    print(output)
    collecting = True
    output = "Just set collecting variable to true, should be true now: " + str(collecting) + "\n"
    os.write(log_file, output)
    print(output)
    # 15 minutes = 900 seconds
    FIFTN_MINUTES_N_SECS = 900

    threading.Timer(FIFTN_MINUTES_N_SECS, get_data).start()

    for table in tables:
        collect_data(table)
        output = "Collecting data: " + str(table) + "\n"
        os.write(log_file, output)
        print(output)

    output = "Setting collecting variable to false, should be true: " + str(collecting) + "\n"
    os.write(log_file, output)
    print(output)
    collecting = False
    output = "Just set collecting variable to false, should be false now: " + str(collecting) + "\n"
    os.write(log_file, output)
    print(output)
    return 0


def main():
    """
    " Main function of the program, opens stream and allows plot to update.
    """
    global collecting
    global dataTable
    global depth2_link
    global log_file
    global stream_link
    global tables
    global temp_link
    global turb2_link
    global turb3_link
    # Open connection to plot.ly server
    stream_link.open()
    turb2_link.open()
    turb3_link.open()
    temp_link.open()
    depth2_link.open()
    output = "plotly streams opened\n"
    os.write(log_file, output)
    print(output)
    median_link.open()
    # Collect data every 15 minutes
    get_data()
    output = "Got data!\n"
    os.write(log_file, output)
    # Update plot continuously
    while True:
        if not collecting:
            try:
                update_plot(dataTable)
                output = "updated plot\n"
                os.write(log_file, output)
            except NoDeviceException, e:
                exception_output = time.strftime("%H:%M:%S") + " In Main Exception occurred: " + str(e) + "\n"
                os.write(log_file, exception_output)
                print(exception_output)
                # Try to continue
                pass
            # Wait 5 seconds before updating
            time.sleep(5)
            # Keep link alive
            #stream_link.heartbeat()
            #output = "heartbeat sent "
            #os.write(log_file, output)
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
    median_link.close()
    depth2_link.close()
    temp_link.close()
    turb3_link.close()
    turb2_link.close()
    stream_link.close()
    output = "Plotly Streams closed\n "
    os.write(log_file, output)
    print(output)
    return 0

# Call main, execute program
try:
    main()
except Exception, e:

    # Log exception
    exception_output = time.strftime("%H:%M:%S") + " Exception occurred: " + str(e) + "\n"
    os.write(log_file, exception_output)
    print(exception_output)
    # Upload logfile
    emergency_put()
    # Try to continue
    pass
