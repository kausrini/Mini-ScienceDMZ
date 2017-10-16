#!/usr/bin/env python3

import os

TOMCAT_VERSION = '8.5.23'
GUACAMOLE_VERSION = '0.9.13'
MYSQL_CONNECTOR_VERSION = '5.1.44'

SQL_CONTAINER_NAME = 'sql_container'
GUACAMOLE_CONTAINER_NAME = 'guacamole_container'
SQL_IMAGE_NAME = 'sql_image'
GUACAMOLE_IMAGE_NAME = 'guacamole_image'
FILE_NAME = 'administrator.txt'

DIRECTORY_BASE = 'base'
DIRECTORY_DATABASE = 'database'
DIRECTORY_GUACAMOLE = 'guacamole'
DIRECTORY_GENERATED_FILES = 'generated_files'

# CAS Extension parameters for Guacamole
CAS_AUTHORIZATION_ENDPOINT = 'https://cas.iu.edu/cas'
CAS_REDIRECT_URI = 'https://mini-science-dmz.dynv6.net/guacamole/'
# Note : CAS_REDIRECT_URI needs to be changed to http instead of https and also port 8080 need to be there
# if proxy server not configured.


# Establishes the file directory to be used
# base directory is the file path where this python script is located
# database directory is the file path where files required for building database container are located
# guacamole directory is the file path where files required for building guacamole container are located
def fetch_file_directories():
    base_directory = os.path.dirname(os.path.realpath(__file__))
    directories = {
        DIRECTORY_BASE : base_directory,
        DIRECTORY_DATABASE : base_directory + '/db',
        DIRECTORY_GUACAMOLE : base_directory + '/dock',
        DIRECTORY_GENERATED_FILES : base_directory + '/generated_files'
    }
    return directories
