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

trace1 = Scatter(
    x=[],
    y=[],
    mode='lines+markers',
    stream=stream_obj
)

data = Data([trace1])

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


def get_csv_data(filepath, row_id, row_num):
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

NTU = get_csv_data('./data/TableEachScan.csv', 'TurbNTU', 0)
Date = get_csv_data('./data/TableEachScan.csv', 'Datetime', 0)

lastLine = Date.size
print("Last line read was: " + str(lastLine))

stream_link.open()

i = 0
N = Date.size

time.sleep(5)

while i < N:
    x = Date[i]
    y = NTU[i] 
    stream_link.write(dict(x=x, y=y))
    i += 1
    if i == N:
        i = 0
        NTU = []
        Date = []
        NTU = get_csv_data('./data/TableEachScan.csv', 'TurbNTU', lastLine + 1)
        Date = get_csv_data('./data/TableEachScan.csv', 'Datetime', lastLine + 1)
        lastLine = lastLine + Date.size
        print("New data EOL is: " + str(lastLine))
        N = Date.size
    time.sleep(0.50)

stream_link.close()
