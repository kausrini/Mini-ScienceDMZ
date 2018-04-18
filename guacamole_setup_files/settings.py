#!/usr/bin/env python3

import os

# Change to appropriate domain name
DOMAIN_NAME = ''

GUACAMOLE_VERSION = '0.9.14'
MYSQL_CONNECTOR_VERSION = '5.1.46'

SQL_CONTAINER_NAME = 'sql_container'
GUACAMOLE_CONTAINER_NAME = 'guacamole_container'
SQL_IMAGE_NAME = 'sql_image'
GUACAMOLE_IMAGE_NAME = 'guacamole_image'

DIRECTORY_BASE = 'base'
DIRECTORY_DATABASE = 'database'
DIRECTORY_GUACAMOLE = 'guacamole'
DIRECTORY_GENERATED_FILES = 'generated_files'
DIRECTORY_LOG_EMAIL = 'log_email'


# Establishes the file directory to be used
# base directory is the file path where this python script is located
# database directory is the file path where files required for building database container are located
# guacamole directory is the file path where files required for building guacamole container are located
def fetch_file_directories():
    base_directory = os.path.dirname(os.path.realpath(__file__))
    directories = {
        DIRECTORY_LOG_EMAIL: base_directory + '/..' + '/log_email',
        DIRECTORY_BASE : base_directory,
        DIRECTORY_DATABASE : base_directory + '/db',
        DIRECTORY_GUACAMOLE : base_directory + '/dock',
        DIRECTORY_GENERATED_FILES : base_directory + '/..' + '/generated_files'
    }
    return directories
