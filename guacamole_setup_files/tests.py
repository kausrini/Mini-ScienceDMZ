#!/usr/bin/env python3

import os
from urllib.request import urlopen
from urllib.error import HTTPError
import sys

import requests

import settings


# Checks if expected directory structure is present and checks for all the required files
def check_directories_files(directories):
    print("Checking if all the required files exist")
    success = True
    for _, directory in directories.items():
        if not os.path.exists(directory):
            print("Error. The folder " + directory + ' is missing')
            success = False

    if not os.path.isfile(directories[settings.DIRECTORY_GUACAMOLE] + '/Dockerfile'):
        print('Error, the setup.sh file is missing from the dock folder')
        success = False

    if not os.path.isfile(directories[settings.DIRECTORY_DATABASE] + '/Dockerfile'):
        print('Error, the Dockerfile is missing from the db folder')
        success = False

    if not os.path.isfile(directories[settings.DIRECTORY_DATABASE] + '/db_init_scripts.sh'):
        print('Error, the db_init_scripts.sh file is missing from the db folder')
        success = False

    if not success:
        print("Fix the issues and re-run the application")
        sys.exit()

    print("All required files are present")


def url_exists(url):

    try:
        response_code = requests.head(url).status_code
    except requests.ConnectionError:
        print("[Error] There were connection problems.")
        return False
    except requests.HTTPError:
        print("[Error] Http Error.")
        return False
    except requests.Timeout:
        print("[Error] Timeout Occurred.")
        return False
    except requests.TooManyRedirects:
        print("[Error] Too many redirects")
        return False
    except requests.RequestException:
        print("[Error] Generic exception")
        return False

    if response_code is 200:
        return True

    return False


# This function is used to check if all the links specified in the Dockerfile(s) are valid.
# Todo: create clear instructions to fix link related errors
def check_dockerfile_links(base_directory):
    success = True
    # Following links are present in the guacamole Dockerfile
    # The guacamole_jdbc link exists in both guacamole Dockerfile and database Dockerfile

    tomcat = (
        "https://www-us.apache.org/dist/tomcat/tomcat-8/v{}"
        "/bin/apache-tomcat-{}"
        ".tar.gz"
    ).format(settings.TOMCAT_VERSION, settings.TOMCAT_VERSION)

    guacamole_server = (
        'http://apache.mirrors.tds.net/incubator/guacamole/{}' 
        '-incubating/source/guacamole-server-{}' 
        '-incubating.tar.gz'
    ).format(settings.GUACAMOLE_VERSION,settings.GUACAMOLE_VERSION)

    guacamole_client = (
        'http://apache.mirrors.tds.net/incubator/guacamole/{}'
        '-incubating/binary/guacamole-{}-incubating.war'
    ).format(settings.GUACAMOLE_VERSION, settings.GUACAMOLE_VERSION)

    guacamole_cas = (
        'http://apache.mirrors.tds.net/incubator/guacamole/{}'
        '-incubating/binary/guacamole-auth-cas-{}-incubating.tar.gz'
    ).format(settings.GUACAMOLE_VERSION, settings.GUACAMOLE_VERSION)

    mysql_connector = (
        'https://cdn.mysql.com//Downloads/Connector-J/mysql-connector-java-{}.tar.gz'
    ).format(settings.MYSQL_CONNECTOR_VERSION)

    guacamole_jdbc = (
        'http://apache.mirrors.lucidnetworks.net/incubator/guacamole/{}'
        '-incubating/binary/guacamole-auth-jdbc-{}-incubating.tar.gz'
    ).format(settings.GUACAMOLE_VERSION, settings.GUACAMOLE_VERSION)

    if not url_exists(tomcat):
        success = False
        print('[Error] The link {} specified in the Guacamole Dockerfile is invalid.'.format(tomcat))

    if not url_exists(guacamole_server):
        success = False
        print('[Error] The link {} specified in the Guacamole Dockerfile is invalid.'.format(guacamole_server))

    if not url_exists(guacamole_client):
        success = False
        print('[Error] The link {} specified in the Guacamole Dockerfile is invalid.'.format(guacamole_client))

    if not url_exists(guacamole_cas):
        success = False
        print('[Error] The link {} specified in the Guacamole Dockerfile is invalid.'.format(guacamole_cas))

    if not url_exists(mysql_connector):
        success = False
        print('[Error] The link {} specified in the Guacamole Dockerfile is invalid.'.format(mysql_connector))

    if not url_exists(guacamole_jdbc):
        success = False
        print('[Error] The link {} specified in the Guacamole Dockerfile and in the Database Dockerfile are invalid.'
              .format(guacamole_jdbc))

    if not success:
        print('Fix the above errors and re-run the application')
        sys.exit()
    else:
        print('All links specified in the Dockerfiles are valid')


def run_tests():
    directories = settings.fetch_file_directories()
    check_directories_files(directories)
    check_dockerfile_links(directories[settings.DIRECTORY_BASE])
    print("All tests are complete and were successful")


if __name__ == '__main__':
    run_tests()
