#!/bin/bash

##
# Creates a reverse tunnel to the central server to allow connection to device in field.
##
createTunnel() {
  # Create reverse SSH session
  /usr/bin/ssh -i keyp1.pem -N -R 19999:localhost:22 ubuntu@aws.cwardcode.com
  # Print result
  if [[ $? -eq 0 ]]; then
    echo Tunnel to Server created successfully
  else
    echo An error occurred creating a tunnel to server. RC was $?
  fi
}
#Get PID of ssh instance
/bin/pidof ssh
# If ssh failed, reconnect
if [[ $? -ne 0 ]]; then
  echo Creating new tunnel connection
  createTunnel
fi
