#!/usr/bin/env python3

import sys
import socket
import os

import shutil

# Store your registered Domain name here.
DOMAIN_NAME = ''

# Note how the url ends in cas. It MUST BE the base cas server.
# Do not use the CAS login url (Ex : https://cas.iu.edu/cas/login or https://www.purdue.edu/apps/account/cas/login)
CAS_AUTHORIZATION_ENDPOINT = 'https://cas.iu.edu/cas'
CAS_VALIDATION_ENDPOINT = CAS_AUTHORIZATION_ENDPOINT + '/serviceValidate'


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


# If no backup file exists, the method creates backup file.
# If backup file does exist, it overwrites original file with the backup.
def backup_file(original_file_name):

    # Generating a backup file name
    try:
        file_extension_position = original_file_name.index('.')
    except ValueError:
        # File has no extension
        file_extension_position = -1

    if file_extension_position == -1:
        backup_file_name = original_file_name + '_backup'
    else:
        backup_file_name = original_file_name[:file_extension_position] + '_backup' \
                           + original_file_name[file_extension_position:]

    if not os.path.isfile(backup_file_name):
        shutil.copy2(original_file_name, backup_file_name)
    else:
        shutil.copy2(backup_file_name, original_file_name)
