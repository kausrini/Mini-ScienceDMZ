#!/usr/bin/env python2.7

import os

TOMCAT_VERSION = '8.5.20'
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


# Establishes the file directory to be used
# base directory is the file path where this python script is located
# database directory is the file path where files required for building database container are located
# guacamole directory is the file path where files required for building guacamole container are located
def fetch_file_directories():
    base_directory = os.path.dirname(os.path.realpath(__file__))
    directories = {
        DIRECTORY_BASE : base_directory,
        DIRECTORY_DATABASE : base_directory + '/db',
        DIRECTORY_GUACAMOLE : base_directory + '/dock'
    }
    return directories