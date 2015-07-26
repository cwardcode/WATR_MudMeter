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
    location = "dev/ttyO4"
elif platform == 'Windows':
    location = "COM1"
else:
    location = "COM1"
# Holds the port on which we're communicating with the device
port = "115200"
# Holds the column names containing data we're monitoring
dataColm = 'TurbNTU_Med'
dataColm2 = 'TurbNTU2_Med'
dataColm3 = 'TurbNTU3_Med'
tempColm = 'AquiTemp_Med'
depthColm = 'DepthFT_Med'
depthColm2 = 'DepthFT2_Med'
# Holds the table that contains the data we're plotting
dataTable = 'Table'
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
    name="Analite Sensor 1 (NTU)"
)

turbidity2 = Scatter(
    x=[],
    y=[],
    mode='lines+markers',
    stream=Stream(
        token=stream_ids[1],
        maxpoints=80
    ),
    name="Analite Sensor 2 (NTU)"
)

turbidity3 = Scatter(
    x=[],
    y=[],
    mode='lines+markers',
    stream=Stream(
        token=stream_ids[2],
        maxpoints=80
    ),
    name="AquiStar Turbo (NTU)"
)


temperature = Scatter(
    x=[],
    y=[],
    mode='lines+markers',
    stream=Stream(
        token=stream_ids[3],
        maxpoints=80
    ),
    name="AquiStar Temp (Deg C)"
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

depth2 = Scatter(
    x=[],
    y=[],
    mode='lines+markers',
    stream=Stream(
        token=stream_ids[5],
        maxpoints=80
    ),
    name="Depth2 (ft)"
)
# Set up data sets
plot_data = Data([turbidity, turbidity2, turbidity3, temperature, depth, depth2])

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
unique_url = py.plot(fig, filename='WATRDataStream_Medians')
# Holds the connections to the streams
stream_link = py.Stream(stream_id)
turb2_link = py.Stream(stream_ids[1])
turb3_link = py.Stream(stream_ids[2])
temp_link = py.Stream(stream_ids[3])
depth_link = py.Stream(stream_ids[4])
depth2_link = py.Stream(stream_ids[5])

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
    global depth_link
    global depth2_link

    # Start date for data  collection, should be fifteen minutes in the past
    sTime = datetime.now() - timedelta(seconds=7)

    # End date for  data collection, should be now, to complete our 15 minute interval
    eTime = datetime.now()

    # Get new data from the logger
    newData = device.get_data(table, sTime, eTime)

    for i in newData:
        x = i[dateColm]
        y = i[dataColm]

        output = "Plotting: Date: " + str(x) + ", NTU: " + str(y)
        print(output)

        os.write(log_file, output)
        stream_link.write(dict(x=x, y=i[dataColm]))
        turb2_link.write(dict(x=x, y=i[dataColm2]))
        turb3_link.write(dict(x=x, y=i[dataColm3]))
        temp_link.write(dict(x=x, y=i[tempColm]))
        depth_link.write(dict(x=x, y=i[depthColm]))
        depth2_link.write(dict(x=x, y=i[depthColm2]))
        time.sleep(0.80)

    return 0


def collect_data(table_name):
    """
    " Function which takes in a table name, gathers its data and exports it as a CSV file for analysis.
    " @:param table_name - name of table to collect data and export
    """
    global has_ran
    
    # Start date for data  collection, should be fifteen minutes in the past
    start_date_form = datetime.now() - timedelta(minutes=15)

    # End date for  data collection, should be now, to complete our 15 minute interval
    end_date_form = datetime.now()

    if platform == 'Linux':
        table_file = os.open(table_name + '.csv', os.O_WRONLY | os.O_APPEND | os.O_CREAT)
    else:
        table_file = os.open(table_name + '.csv', os.O_BINARY | os.O_WRONLY | os.O_APPEND | os.O_CREAT)
    table_data = device.get_data(table_name, start_date_form, end_date_form)
    if has_ran:
        table_csv = utils.dict_to_csv(table_data, ",", header=False)
    else:
        table_csv = utils.dict_to_csv(table_data, ",", header=True)
        has_ran = True

    os.write(table_file, table_csv.encode('UTF-8'))
    os.close(table_file)

    # Upload/Append data to server
    put_data(table_name)

    return 0


def put_data(file_name):
    """
    " Uploads new data to server via ssh
    """
    loc_file = open(file_name + '.csv', 'rw')
    # Holds private key to connect to server
    key = paramiko.RSAKey.from_private_key_file('keyp1.pem')
    # Holds Transport socket
    t = paramiko.Transport(('aws.trantracker.com', 22))
    # Attempt to connect with key
    t.connect(username='ubuntu', pkey=key)
    # Create sftp session
    c = paramiko.SFTPClient.from_transport(t)
    # Change into where data is stored
    c.chdir('updata')
    # Get remote file, and set mode to append
    rem_file = c.file(file_name + '.csv', mode='a', bufsize=1)
    # Write data and clean up
    rem_file.write(loc_file.read())
    rem_file.flush()
    rem_file.close()
    loc_file.close()
    os.remove(file_name + '.csv')


def get_data():
    """
    " Collects data from the logger every 15 minutes and stores in file to send
    """
    global collecting
    global tables

    collecting = True
    # 15 minutes = 900 seconds
    FIFTN_MINUTES_N_SECS = 900

    threading.Timer(FIFTN_MINUTES_N_SECS, get_data).start()

    for table in tables:
        collect_data(table)
    collecting = False
    
    return 0


def main():
    """
    " Main function of the program, opens stream and allows plot to update.
    """
    global collecting
    global dataTable
    global log_file
    global stream_link
    global turb2_link
    global turb3_link
    global temp_link
    global depth_link
    global depth2_link

    # Open connection to plot.ly server
    stream_link.open()
    turb2_link.open()
    turb3_link.open()
    temp_link.open()
    depth_link.open()
    depth2_link.open()
    # Collect data every 15 minutes
    get_data()
    # Update plot continuously
    while True:
        if not collecting:
            update_plot(dataTable)
            # Wait 5 seconds before updating
            time.sleep(5)
            # Keep link alive
            stream_link.heartbeat()
        else:
            output = "waiting to finish sending data"
            print(output)
            os.write(log_file, output)
            # Wait 15 seconds to finish sending data
            time.sleep(15)
    # Close stream to server
    depth2_link.close()
    depth_link.close()
    temp_link.close()
    turb3_link.close()
    turb2_link.close()
    stream_link.close()
    return 0

# Call main, execute program
try:
    main()
except Exception, e:
    exception_output = "Exception occurred: " + str(e)
    os.write(log_file, exception_output)
    print(exception_output)
    pass
