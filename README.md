# CampbellDataStreaming
##Description
- A system allowing data collection from a Campbell scientific datalogger using
  a BeagleBone Black and Python, and automatically streaming data statistics to plot.ly.

##Requirements:
- BeagleBone Black running Debian Jessie
- Internet Connection (I'm using a GSM Modem)
- UART4 RS232 cape

##To start logging:
1. Clone repo
2. Run DataCollection/setup.sh as sudo

Folder Layout:
 -DataCollection <- Forked from CampbellDataCollection repository
 -Streaming      <- Contains data streaming code
