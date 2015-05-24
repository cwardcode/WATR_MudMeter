from plotly.graph_objs import Stream, Scatter, Layout, Data, Figure, XAxis,YAxis
import csv
import plotly.plotly as py
import plotly.tools as tls
import numpy as np
import time


stream_ids = tls.get_credentials_file()['stream_ids']

stream_id = stream_ids[0]

stream_obj = Stream(
    token=stream_id,
    maxpoints=80
)

turbidity = Scatter(
    x=[],
    y=[],
    mode='lines+markers',
    stream=stream_obj,
    name="Turbidity (NTU)"
)

data = Data([turbidity])

layout = Layout(
    title='NTU Over Time',
    xaxis=XAxis(
        title='Date Time'
    ),
    yaxis=YAxis(
        title='Turbidity(NTU)'
    )
)

fig = Figure(data=data, layout=layout)

unique_url = py.plot(fig, filename='NTUDataStream')

stream_link = py.Stream(stream_id)

lastLine = 0
firstPass = True

def get_csv_data(filepath, row_id, row_num):
    data_array = []
    with open(filepath, 'r') as data_file:
        reader = csv.reader(data_file)
        hrow = reader.next()
        colid = hrow.index(row_id)
        while reader.line_num != (row_num + 1):
            reader.next()
        for row in reader:
            print("Getting Row:" + str(row[colid]))
            data_array.append(row[colid])
        nparray = np.array(data_array)
        return nparray

def update_plot(line):
    global stream_link
    global lastLine
    global firstPass

    NTU = None
    Date = None

    if firstPass:
        print("first pass!")
        NTU = get_csv_data('./examples/small/d1.csv', 'TurbNTU', 0)
        Date = get_csv_data('./examples/small/d1.csv', 'Datetime', 0)
        firstPass = False
        lastLine = Date.size
    else:

        print("Not second pass.. Line is: " + str(line))
        NTU = get_csv_data('./examples/small/d1.csv', 'TurbNTU', line)
        print("Just got NTU = " + str(NTU))
        Date = get_csv_data('./examples/small/d1.csv', 'Datetime', line)
        print("Just got Date = " + str(Date))
    lastLine = Date.size + line
    print("lastLine = " + str(lastLine))

    i = 0
    N = lastLine + line
    print("N = " + str(N))
    print("NTU = " + str(NTU))
    print("Date = " + str(Date))
    time.sleep(5)
    while i < N:
        x = Date[i]
        y = NTU[i]
        print("Plotting: Date: " + str(x) + ", NTU: " + str(y))
        stream_link.write(dict(x=x, y=y))
        i += 1
        if i == N:
            i = 0
            NTU = None
            Date = None
            print("i = n getting new data! lastLine: " + str(lastLine + 1))
            # NTU = get_csv_data('./data/TableEachScan.csv', 'TurbNTU', lastLine + 1)
            # Date = get_csv_data('./data/TableEachScan.csv', 'Datetime', lastLine + 1)
            NTU = get_csv_data('./examples/small/d1.csv', 'TurbNTU', lastLine + 1)
            Date = get_csv_data('./examples/small/d1.csv', 'Datetime', lastLine + 1)
            print("NTU has: " + str(NTU))
            lastLine = lastLine + Date.size
            print("New data EOF is: " + str(lastLine))
            N = Date.size
        time.sleep(0.50)

stream_link.open()

while True:
    try:
        update_plot(lastLine)
    except StopIteration:
        print("oops! out of data to send :( Waiting 30 seconds and trying again!")
        time.sleep(5)
        pass

stream_link.close()
