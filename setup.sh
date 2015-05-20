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
# 4  - Could not copy file
# 5  - Failed to create directory
# 6  - Failed to install packages
# 7  - Failed to install pip
# 8  - Failed to install python module pycampbellcr1000
# 9  - Failed to set cron job
# 10 - Failed to set allowed user for incron
# 11 - Failed to set incron job
##

#Path to install system
installPath=/root/bin

# Ensure all required files are present
if [ ! -f "send_data.sh"  -o ! -f "DataCollection.py" ]
then
    echo "Required files are missing!"
    exit 1
fi

# Check if user has root
sudo=$(whoami)
if [ $sudo != "root" ]
then
    echo "Must run script as root or via sudo!"
    exit 2
fi

# Enable UART 4 in uEnv.txt
uartStat=$(echo dtb=am335x-boneblack-ttyO4.dtb >> /boot/uEnv.txt)
if [ $? -ne 0 ]
then
    echo -e "$uartStat\nFailed to setup uart4 support, exiting."
    exit 2
fi

# Create and move required files to bin dir in /root/
if [ -d $installPath ]
then
    # Try copying files over
    copyStat=$(cp send_data.sh DataCollection.py $installPath)
    # If files fail to copy, exit.
    if [ $? -ne 0 ]
    then
        echo -e "$copyStat\nFailed to copy, exiting."
        exit 2
    fi
else
    #Try to create bin directory
    mkdirStat=$(mkdir $installPath)
    if [ $? -ne 0 ]
    then
        echo -e "$mkdirStat \nDirectory could not be created, exiting."
        exit 3
    fi
    copyStat=$(cp send_data.sh DataCollection.py $installPath)
    if [ $? -ne 0 ]
    then
        echo -e "$copyStat\nFailed to copy, exiting."
        exit 2
    fi
fi

# Install all required packages
aptStat=$(sudo apt-get -y install python incron)
if [ $? -ne 0 ]
then
    echo -e "$aptStat\nFailed to install required packages, exiting."
    exit 4
fi

# Install pip, the python package manager
wget https://bootstrap.pypa.io/get-pip.py
pipStat=$(python get-pip.py)
if [ $? -ne 0 ]
then
    echo -e "$pipStat\nFailed to install pip, exiting."
    rm get-pip.py
    exit 5
fi
rm get-pip.py

# Install required python module
pycamStat=$(pip install pycampbellcr1000)
if [ $? -ne 0 ]
then
    echo -e "$pycamStat\nFailed to install python module, exiting."
    exit 6
fi

#TODO: ensure job doesn't already exist
#setup cron to run script every 15 minutes
cronStat=$(echo -e "*/15 *  * * *   root    python $installPath/DataCollection.py" >> /etc/crontab)
if [ $? -ne 0 ]
then
    echo -e "$cronStat\nFailed to set cron job, exiting."
    exit 7
fi

#setup incron to auto-upload data
incronUserStat=$(echo -e "root" >> /etc/incron.allow)
if [ $? -ne 0 ]
then
    echo -e "$incronUserStat\nFailed to set user in incron, exiting."
    exit 8
fi

incronStat=$(echo -e "/root IN_MODIFY,IN_CREATE,IN_MOVED_TO $installPath/send_data.sh" >> /var/spool/incron/root)
if [ $? -ne 0 ]
then
    echo -e "$camStat\nFailed to set incron job, exiting."
    exit 9
fi

echo "Restarting services.."
cronResStatus=$(sudo service cron restart)
if [ $? -ne 0 ]
then
    echo -e "$cronResStatus\nFailed to restart cron, exiting."
    exit 10
fi
incronResStatus=$(sudo service incron restart)
if [ $? -ne 0 ]
then
    echo -e "$incronStatus\nFailed to restart incron, exiting."
    exit 11
fi

echo "Setup complete!"
exit 0
