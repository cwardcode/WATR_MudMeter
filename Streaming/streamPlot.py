from plotly.graph_objs import *
import csv
import datetime
import plotly.plotly as py
import plotly.tools as tls
import numpy as np
import time

stream_ids = tls.get_credentials_file()['stream_ids']

stream_id=stream_ids[0]

stream = Stream(
        token=stream_id,
        maxpoints=80
)

trace1 = Scatter(
        x=[],
        y=[],
        mode='lines+markers',
        stream=stream
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

def get_csv_data(filepath, row_id):
    data = []
    with open(filepath, 'r') as data_file:
        reader = csv.reader(data_file)
        hrow = reader.next()
        colID = hrow.index(row_id)
        for row in reader:
            data.append(row[colID])
        npArray = np.array(data)
        return npArray

NTU = get_csv_data('./data/TableEachScan.csv','TurbNTU')
Date = get_csv_data('./data/TableEachScan.csv','Datetime')

stream_link.open()

i = 0
k = 5
N = Date.size

time.sleep(5)

while i<N:
    x = Date[i]
    y = NTU[i] 
    stream_link.write(dict(x=x, y=y))
    i += 1
    if i == N:
	i=0
	NTU = get_csv_data('./data/TableEachScan.csv','TurbNTU')
	Date = get_csv_data('./data/TableEachScan.csv','Datetime')
      	print("New data loaded: " + str(NTU)) 
    #time.sleep(0.08)
    time.sleep(1.00)

stream_link.close()

