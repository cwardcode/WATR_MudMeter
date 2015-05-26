##
# Author:      Chris Ward
# Date:        05/26/2015
# Version:     05/26/2015
# Description: An attempt to read in data from our CR850 data logger and stores
#           to files based on table name, while streaming to plot.ly
##

from datetime import datetime, timedelta
from plotly.graph_objs import Stream, Scatter, Layout, Data, Figure, XAxis,YAxis
from pycampbellcr1000 import CR1000, utils
import csv
import platform
import plotly.plotly as py
import plotly.tools as tls
import numpy as np
import os
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
# The device we're connecting to,
time1=datetime.now()
print("waiting to connect to device... Time start: " + str(time1))
device = CR1000.from_url('serial:/' + location + ":" + port)
time2=datetime.now()
print("connected, time taken to connect: "+ str(time2-time1))
# Get Streaming Tokens from plot.ly
stream_ids = tls.get_credentials_file()['stream_ids']
# Grab first Token in list
stream_id = stream_ids[0]
# Create the stream
stream_obj = Stream(
    token=stream_id,
    maxpoints=80
)

# Set up our plot
turbidity = Scatter(
    x=[],
    y=[],
    mode='lines+markers',
    stream=stream_obj,
    name="Turbidity (NTU)"
)

# Set up data sets
data = Data([turbidity])

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
fig = Figure(data=data, layout=layout)
# Generate plot.ly URL based on name
unique_url = py.plot(fig, filename='NTUDataStream-Testing')
# Holds the connection to the stream
stream_link = py.Stream(stream_id)
# Holds the last line read in the file
lastLine = 0
# Holds whether the file has been read
firstPass = True

# Holds location to the data set
#dataFile = '.\data\TableEachScan.csv'
# Holds the column name containing data we're monitoring
dataColm = 'TurbNTU'
# Holds the column name containing the date
dateColm = 'Datetime'
# Holds starting index value
startIndex = 0
updating = False
def update_plot(table):
    """
    " update_plot: Updates the plot.ly plot with new data continuously
    " @:argument line - the line number last read from the previous call
    """
    print("update_plot called")
    global stream_link
    global lastLine
    global dataFile
    global dataColm
    global dateColm
    global firstPass
    global fpTimer
    global startIndex
    global device
    global updating
    
    updating = True
    
    # Start date for data  collection, should be fifteen minutes in the past
    start_date_form = datetime.now() - timedelta(seconds=5)

    # End date for  data collection, should be now, to complete our 15 minute interval
    end_date_form = datetime.now()
    
    # Get new data from the logger
    newData = device.get_data(table,start_date_form,end_date_form)
    
    seen = set()
    deDupData = []
    for d in newData:
        row = tuple(d.items())
        if row not in seen:
            seen.add(row)
            deDupData.append(d)
    print("obtained data")
    for i in deDupData:
        x = i['Datetime']
        y = i['TurbNTU']
        print("Plotting: Date: " + str(x) + ", NTU: " + str(y))
        stream_link.write(dict(x=x, y=y), dict(title="NTU Over Time"))
        time.sleep(0.80)
    updating=False

"""
" Main function of the program, opens stream and allows plot to update.
"""
def main():
    global stream_link
    global lastLine
    global updating
    # Open connection to plot.ly server
    stream_link.open()
    # Infinitely collect data
    while True and not updating:
        update_plot('TableEachScan')
        #Wait 5 seconds before updating
        time.sleep(5)
        stream_link.heartbeat()
            

    # Close stream to server
    stream_link.close()

# Call main, execute program
# catch any exception TODO: fix
try:
    main()
except Exception:
    print("Exception occurred")
    pass
