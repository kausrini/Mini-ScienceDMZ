#!/usr/bin/env python3

import sys
import socket
import os

# Store your registered Domain name here.
DOMAIN_NAME = ''


# Checks if valid values entered for setup settings in pi_settings.py file
def test_values():

    if not len(DOMAIN_NAME):
        print('[ERROR] The pi_settings.py file does not have a valid DOMAIN_NAME.\n'
              'Check the instructions for DOMAIN_NAME in the Readme file'
              )
        sys.exit()


# Checks internet connectivity by trying tcp connect to archive.raspberrypi.org
# Fails in case archive.raspberrypi.org is down (highly unlikely) or if dns resolver fails
def check_internet_connectivity():
    print('Testing Internet Connectivity')
    connected = False
    try:
        host = 'archive.raspberrypi.org'
        socket.create_connection((host, 80))
        connected = True
    except OSError:
        pass

    if not connected:
        print('[ERROR] No internet connectivity. Please check if the raspberry pi has a network connection')
        return False

    print('The raspberry pi has internet connectivity.')
    return True
