from plotly.graph_objs import Stream, Scatter, Layout, Data, Figure, XAxis,YAxis
import csv
import plotly.plotly as py
import plotly.tools as tls
import numpy as np
import time


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
unique_url = py.plot(fig, filename='NTUDataStream')
# Holds the connection to the stream
stream_link = py.Stream(stream_id)
# Holds the last line read in the file
lastLine = 0
# Holds whether the file has been read
firstPass = True
# 5 second timer
fpTimer = True
# Holds location to the data set
dataFile = './examples/small/d1.csv'
# Holds the column name containing data we're monitoring
dataColm = 'TurbNTU'
# Holds the column name containing the date
dateColm = 'Datetime'
# Holds starting index value
startIndex = 0


def get_csv_data(filepath, row_id, row_num):
    """
    " get_csv_data: Gets data from a csv file
    " @:argument filepath - path to csv file
    " @:argument row_id - Name of column to collect data
    " @:argument row_num - line number to start reading from
    " @:return an nparray of all collected data
    """
    data_array = []
    with open(filepath, 'r') as data_file:
        reader = csv.reader(data_file)
        hrow = reader.next()
        colid = hrow.index(row_id)
        while reader.line_num != (row_num + 1):
            reader.next()
        for row in reader:
            data_array.append(row[colid])
        nparray = np.array(data_array)
        return nparray


def update_plot(line):
    """
    " update_plot: Updates the plot.ly plot with new data continuously
    " @:argument line - the line number last read from the previous call
    """
    global stream_link
    global lastLine
    global dataFile
    global dataColm
    global dateColm
    global firstPass
    global fpTimer
    global startIndex

    """
    " Check to see if it is the first time this method was called, so we can
    " keep track of where to read data from. If first pass, start reading at 0.
    """
    if firstPass:
        NTU = get_csv_data(dataFile, dataColm, startIndex)
        Date = get_csv_data(dataFile, dateColm, startIndex)
        firstPass = False
        lastLine = Date.size
    else:
        print("Loading new, starting from line: " + str(line))
        stream_link.write(dict(), dict(title="NTU Over Time (Waiting for new data)"))
        NTU = get_csv_data(dataFile, dataColm, line)
        print("Just got NTU = " + str(NTU))
        Date = get_csv_data(dataFile, dateColm, line)
        print("Just got Date = " + str(Date))
        lastLine = Date.size + line
    print("lastLine = " + str(lastLine))

    # (Re)set counter to 0
    i = 0
    # Set N to be size of data loaded
    N = Date.size

    print("N = " + str(N))
    print("NTU = " + str(NTU))
    print("Date = " + str(Date))

    # Wait for 5 seconds for tab to reload
    if fpTimer:
        time.sleep(5)
        fpTimer = False
    else:
        time.sleep(1)

    """
    " Iterate through array and plot points
    """
    while i < N:
        x = Date[i]
        y = NTU[i]
        print("Plotting: Date: " + str(x) + ", NTU: " + str(y))
        stream_link.write(dict(x=x, y=y), dict(title="NTU Over Time"))
        i += 1
        time.sleep(0.80)


# Open connection to plot.ly server
stream_link.open()

# Infinitely collect data
while True:
    try:
        update_plot(lastLine)
    except Exception:
        print("Exception thrown!!!")
        pass

# Close stream to server
stream_link.close()
