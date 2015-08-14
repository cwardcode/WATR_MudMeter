#!/bin/bash

##
# Author: Chris Ward <chris@cwardcode.com>
# Name: DataCollectSetup.sh
# Desc: Setup script to run on new BeagleBone Black to automatically set it up for data collection.
# TODO: allow for custom install paths
#       ensure *cron will not have duplicate jobs
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
# 11 - Failed to set cron job
# 12 - Failed to set allowed user for incron
# 13 - Failed to set incron job
# 14 - Failed to restart cron service
# 15 - Failed to restart incron service
##

# Check if user has root
sudo=$(whoami)
if [ $sudo != "root" ]
then
    echo "Must run script as root or via sudo!"
    exit 2
fi

#Prompt user for install path
read -p "Please enter desired install path [/root/bin]: " installPath
installPath=${installPathath:-/root/bin}
installPathUp=${installPath%/*}
echo -e "Installing to $installPath"

# Ensure all required files are present
echo -n "Verifying install files... "
if [ ! -f "send_data.sh"  -o ! -f "DataCollection.py" -o ! -f "usb3g" -o ! -f "usb4g" ]
then
    echo "Required files are missing!"
    exit 1
fi
echo "ok!"

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
    # Try copying files over
    copyStat=$(cp send_data.sh DataCollection.py $installPath)
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
    copyStat=$(cp send_data.sh DataCollection.py $installPath)
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

#setup cron to run script every 15 minutes
echo -n "Adding data collection job to cron..."
cronStat=$((crontab -l; echo -e "*/15 *  * * *   root    python $installPath/DataCollection.py") | sort - | uniq - | crontab -)
if [ $? -ne 0 ]
then
    echo -e "$cronStat\nFailed to set cron job, exiting."
    exit 11
fi
echo "ok!"

#setup incron to auto-upload data
echo -n "Adding root user to incron..."
incronUserStat=$(echo -e "root" >> /etc/incron.allow)
if [ $? -ne 0 ]
then
    echo -e "$incronUserStat\nFailed to set user in incron, exiting."
    exit 12
fi
echo "ok!"

echo -n "Adding auto-upload to incron..."
incronStat=$((incrontab -l;echo -e "$installPathUp IN_MODIFY,IN_CREATE,IN_MOVED_TO $installPath/send_data.sh") | sort - | uniq - | incrontab -)
if [ $? -ne 0 ]
then
    echo -e "$camStat\nFailed to set incron job, exiting."
    exit 13
fi
echo "ok!"

echo -n "Restarting services.."
cronResStatus=$(sudo service cron restart)
if [ $? -ne 0 ]
then
    echo -e "$cronResStatus\nFailed to restart cron, exiting."
    exit 14
fi
incronResStatus=$(sudo service incron restart)
if [ $? -ne 0 ]
then
    echo -e "$incronStatus\nFailed to restart incron, exiting."
    exit 15
fi
echo "ok!"
echo "Setup complete!"
exit 0
