##
# Author:      Chris Ward
# Date:        05/26/2015
# Version:     05/26/2015
# Description: An attempt to read in data from our CR850 data logger and stores
#           to files based on table name, while streaming to plot.ly
##

from datetime import datetime, timedelta
from plotly.graph_objs import Stream, Scatter, Layout, Data, Figure, XAxis, YAxis
from pycampbellcr1000 import CR1000, utils
import os
import platform
import plotly.plotly as py
import plotly.tools as tls
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
dataColm = 'TurbNTU'
dataColm2 = 'TurbNTU2'
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
# Create the stream
stream_obj = Stream(
    token=stream_id
)

# Set up our traces
turbidity = Scatter(
    x=[],
    y=[],
    mode='lines+markers',
    stream=stream_obj,
    name="Turbidity Sensor (NTU)"
)

turbidity2 = Scatter(
    x=[],
    y=[],
    mode='lines+markers',
    stream=Stream(
        token=stream_ids[1],
    name="Turbidity Sensor 2 (NTU)"
)

# Set up data sets
plot_data = Data([turbidity, turbidity2])

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
unique_url = py.plot(fig, filename='NTUDataStream')
# Holds the connection to the stream
stream_link = py.Stream(stream_id)
turb2_link = py.Stream(stream_ids[1])
# Holds whether update_plot is currently running
collecting = False


def update_plot(table):
    """
    " update_plot: Updates the plot.ly plot with new data continuously
    " @:argument table - the table from which we're collecting data
    """
    global dataColm
    global dataColm2
    global dateColm
    global device
    global stream_link
    global turb2_link

    # Start date for data  collection, should be fifteen minutes in the past
    sTime = datetime.now() - timedelta(seconds=7)

    # End date for  data collection, should be now, to complete our 15 minute interval
    eTime = datetime.now()

    # Get new data from the logger
    newData = device.get_data(table, sTime, eTime)

    for i in newData:
        x = i[dateColm]
        y = i[dataColm]
        y1 = i[dataColm2]
        print("Plotting: Date: " + str(x) + ", NTU: " + str(y))
        stream_link.write(dict(x=x, y=y))
        turb2_link.write(dict(x=x, y=y1))
        time.sleep(0.80)

    return 0


def collect_data(table_name):
    """
    " Function which takes in a table name, gathers its data and exports it as a CSV file for analysis.
    " @:param table_name - name of table to collect data and export
    """
    # Holds whether the file already exists
    exists = False

    # Start date for data  collection, should be fifteen minutes in the past
    start_date_form = datetime.now() - timedelta(minutes=15)

    # End date for  data collection, should be now, to complete our 15 minute interval
    end_date_form = datetime.now()

    os.open('.filelock', os.O_WRONLY | os.O_CREAT)
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
    os.remove('.filelock')
    return 0

def get_data():
    """
    " Collects data from the logger every 15 minutes and stores in file to send
    "
    """
    global collecting
    global tables

    collecting = True
    # 15 minutes = 900 seconds
    FIFTN_MINUTES_N_SECS = 900

    threading.Timer(FIFTN_MINUTES_N_SECS, get_data).start()

    os.open('.datalock', os.O_WRONLY | os.O_CREAT)

    for table in tables:
        collect_data(table)

    os.remove('.datalock')
    collecting = False

    return 0

"""
" Main function of the program, opens stream and allows plot to update.
"""
def main():
    global collecting
    global dataTable
    global stream_link
    global turb2_link

    # Open connection to plot.ly server
    stream_link.open()
    turb2_link.open()
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
            print("waiting to finish sending data")
            # Wait 15 seconds to finish sending data
            time.sleep(15)
    # Close stream to server
    turb2_link.close()
    stream_link.close()
    return 0

# Call main, execute program
try:
    main()
except Exception, e:
    print("Exception occurred: " + str(e))
    pass
