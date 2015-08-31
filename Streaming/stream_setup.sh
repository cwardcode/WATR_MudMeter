#!/bin/bash

##
# Author: Chris Ward <chris@cwardcode.com>
# Name: DataCollectSetup.sh
# Desc: Setup script to run on a Raspberry Pi to automatically set it up for data collection.
# Exit Values:
# 0  - Successfully exited
# 1  - Missing required files
# 2  - User does not have sudo
# 3  - Could not edit uEnv.txt
# 4  - Could not copy services
# 5  - Could not update rc.d
# 6  - Could not copy file
# 7  - Failed to create directory
# 8  - Failed to install packages
# 9  - Failed to install pip
# 10 - Failed to install python module pycampbellcr1000
# 11 - Failed to install paramiko module
# 12 - Failed to set cron job for tunnel script
##

# Check if user has root
sudo=$(whoami)
if [ $sudo != "root" ]
then
    echo "Must run script as root or via sudo!"
    exit 2
fi

#Prompt user for install path
installPath=/bin/stream/
#Get path above where we are now
installPathUp=${installPath%/*}
echo -e "Installing to $installPath"

# Ensure all required files are present
echo -n "Verifying install files are present... "
if [ ! -f "streamPlot.py" -o ! -f "usb3g" -o ! -f "usb4g" -o ! -f "tunnel.sh" ]
then
    echo "Required files are missing!"
    exit 1
fi
echo "ok!"

# Copy tunnel script to /bin
$(cp tunnel.sh /bin/;chmod 755 /bin/tunnel.sh)

# Copy and initialize services
echo -n "Installing services... "
cpStat=$(cp usb* /etc/init.d/)
if [ $? -ne 0 ]
then
    echo -e "$uartStat\nFailed to copy services, exiting."
    exit 4
else
    threeGStat=$(update-rc.d usb3g defaults)
    if [ $? -ne 0 ]
    then
        echo -e "$threeGStat\nFailed to update rc.d for usb3g, exiting."
        exit 5
    fi
    fourGStat=$(update-rc.d usb4g defaults)
    if [ $? -ne 0 ]
    then
        echo -e "$fourGStat\nFailed to update rc.d for usb4g, exiting."
        exit 5
    fi
 
fi
echo "ok!"

# Create and move required files to bin dir in /root/
echo -n "Copying files..."
if [ -d $installPath ]
then
    # Try copying files to install path
    copyStat=$(cp streamPlot.py $installPath)
    # If files fail to copy, exit.
    if [ $? -ne 0 ]
    then
        echo -e "$copyStat\nFailed to copy, exiting."
        exit 6
    fi
else
    #Try to create bin directory
    mkdirStat=$(mkdir -p $installPath)
    if [ $? -ne 0 ]
    then
        echo -e "$mkdirStat \nDirectory could not be created, exiting."
        exit 7
    fi
    copyStat=$(cp streamPlot.py $installPath)
    if [ $? -ne 0 ]
    then
        echo -e "$copyStat\nFailed to copy, exiting."
        exit 5
    fi
fi
echo "ok!"

# Install all required packages
echo -n "Installing required packages..."
aptStat=$(sudo apt-get -y install python incron)
if [ $? -ne 0 ]
then
    echo -e "$aptStat\nFailed to install required packages, exiting."
    exit 8
fi
echo "ok!"

# Install pip, the python package manager
echo -n "Installing Python PIP manager..."
wget -q https://bootstrap.pypa.io/get-pip.py
pipStat=$(python get-pip.py)
if [ $? -ne 0 ]
then
    echo -e "$pipStat\nFailed to install pip, exiting."
    rm get-pip.py
    exit 9
fi
rm get-pip.py
echo "ok!"

# Install required python module
echo -n "Installing PyCampbell module..."
pycamStat=$(pip install pycampbellcr1000)
if [ $? -ne 0 ]
then
    echo -e "$pycamStat\nFailed to install python module, exiting."
    exit 10
fi
echo "ok!"

# Install required python module
echo -n "Installing Parakimo module..."
pycamStat=$(pip install paramiko)
if [ $? -ne 0 ]
then
    echo -e "$pycamStat\nFailed to install paramiko module, exiting."
    exit 11
fi
echo "ok!"

# Setup cron to run tunnel script constantly
echo -n "Adding tunnel script to cron..."
cronStat=$((crontab -l; echo -e " */1 * * * * /bin/tunnel.sh > ~/tunnel.log 2>&1") | sort - | uniq - | crontab - ) 
if [ $? -ne 0 ]
then
    echo -e "$cronStat\nFailed to set cron job, exiting."
    exit 12
fi
echo "ok!"

echo "Setup complete!"
exit 0
