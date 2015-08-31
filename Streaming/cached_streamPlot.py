from plotly.graph_objs import Legend, Font, Stream, Scatter, Layout, Data, Figure, XAxis, YAxis
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

# Set up our plot's traces
turbidity = Scatter(
    x=[],
    y=[],
    mode='lines+markers',
    stream=stream_obj,
    name="Turbidity (NTU)"
)

turbidity2 = Scatter(
    x=[],
    y=[],
    mode='lines+markers',
    stream=Stream(
        token=stream_ids[1],
        maxpoints=80
    ),
    name="Turbidity Sensor 2 (NTU)"
)


# Set up data sets
data = Data([turbidity, turbidity2])

# Configure the Layout
layout = Layout(
    title='NTU Over Time',
    showlegend=True,
    legend=Legend(
        y=0.5,
        font=Font(
            size=12
        )
    ),
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
fftnMinTurb_link = py.Stream(stream_ids[1])
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
dataColm2 = 'TurbNTU2'
# Holds the column name containing the date
datetimeColm = 'Datetime'
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
    global dataColm
    global dataColm2
    global datetimeColm
    global dataFile
    global firstPass
    global fpTimer
    global lastLine
    global startIndex
    global stream_link

    """
    " Check to see if it is the first time this method was called, so we can
    " keep track of where to read data from. If first pass, start reading at 0.
    """
    if firstPass:
        NTU = get_csv_data(dataFile, dataColm, startIndex)
        NTU = get_csv_data(dataFile, dataColm2, startIndex)
        Date = get_csv_data(dataFile, dateColm, startIndex)
        firstPass = False
        lastLine = Date.size
    else:
        stream_link.write(dict(), dict(title="NTU Over Time (Waiting for new data)"))
        NTU = get_csv_data(dataFile, dataColm, line)
        NTU2 = get_csv_data(dataFile, dataColm2, line)
        Date = get_csv_data(dataFile, dateColm, line)
        lastLine = Date.size + line

    # (Re)set counter to 0
    i = 0
    # Set N to be size of data loaded
    N = Date.size
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
        y1 = NTU2[i]
        print("Plotting: Date: " + str(x) + ", NTU: " + str(y))
        stream_link.write(dict(x=x, y=y), dict(title="NTU Over Time (Waiting for new data)"))
        fftnMinTurb_link.write(dict(x=x, y=y1), dict(title="NTU Over Time (Waiting for new data)"))
        i += 1
        time.sleep(0.80)


# Open connection to plot.ly server
stream_link.open()
fftnMinTurb_link.open()

# Infinitely collect data
while True:
    try:
        update_plot(lastLine)
    except Exception:
        print("Exception thrown!!!")
        pass

# Close stream to server
fftnMinTurb_link.close()
stream_link.close()
