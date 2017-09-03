#!/usr/bin/env python2.7

import os
import urllib2

import guac_settings as settings


def check_directories_files(directories):
    print("Checking if all the required files exist")
    success = True
    for _, directory in directories.iteritems():
        if not os.path.exists(directory):
            print("Error. The folder " + directory + ' is missing')
            success = False

    if not os.path.isfile(directories[settings.DIRECTORY_GUACAMOLE] + '/Dockerfile'):
        print('Error, the setup.sh file is missing from the dock folder')
        success = False

    if not os.path.isfile(directories[settings.DIRECTORY_GUACAMOLE] + '/setup.sh'):
        print('Error, the setup.sh file is missing from the dock folder')
        success = False

    if not os.path.isfile(directories[settings.DIRECTORY_DATABASE] + '/Dockerfile'):
        print('Error, the Dockerfile is missing from the db folder')
        success = False

    if not os.path.isfile(directories[settings.DIRECTORY_DATABASE] + '/db_init_scripts.sh'):
        print('Error, the db_init_scripts.sh file is missing from the db folder')
        success = False

    if not os.path.isfile(directories[settings.DIRECTORY_DATABASE] + '/administrator.txt'):
        print('Error, the users.txt file is missing from the db folder. ' +
              'It needs to contain the administrator for guacamole')
        success = False

    if not success:
        print("Fix the issues and re-run the application")
        sys.exit()

    print("All required files are present")


def url_exists(url):
    request = urllib2.Request(url)
    request.get_method = lambda: 'HEAD'
    try:
        response = urllib2.urlopen(url)
        if response.getcode() is 200:
            return True
        else:
            return False
    except urllib2.HTTPError:
        return False


# Todo: Do this (Need to pass guacamole Environment variable)
def check_dockerfile_links(base_directory):

    sucess = True
    # Following links are present in the guacamole Dockerfile
    tomcat = 'https://www-us.apache.org/dist/tomcat/tomcat-8/v{}/bin/apache-tomcat-{}.tar.gz'. \
        format(settings.TOMCAT_VERSION, settings.TOMCAT_VERSION)

    guacamole_server = 'http://apache.mirrors.tds.net/incubator/guacamole/{}' \
                           .format(settings.GUACAMOLE_VERSION) + '-incubating/source/guacamole-server-{}' \
                           .format(settings.GUACAMOLE_VERSION) + '-incubating.tar.gz'

    guacamole_client = 'http://apache.mirrors.tds.net/incubator/guacamole/{}-incubating/binary/guacamole-{}-incubating.war'.format(
        settings.GUACAMOLE_VERSION, settings.GUACAMOLE_VERSION)

    guacamole_cas = 'http://apache.mirrors.tds.net/incubator/guacamole/{}-incubating/binary/guacamole-auth-cas-{}-incubating.tar.gz'.format(
        settings.GUACAMOLE_VERSION, settings.GUACAMOLE_VERSION)

    guacamole_jdbc = 'http://apache.mirrors.lucidnetworks.net/incubator/guacamole/{}-incubating/binary/guacamole-auth-jdbc-{}-incubating.tar.gz'.format(
        settings.GUACAMOLE_VERSION, settings.GUACAMOLE_VERSION)

    mysql_connector = 'https://cdn.mysql.com//Downloads/Connector-J/mysql-connector-java-{}.tar.gz'.format(
        settings.MYSQL_CONNECTOR_VERSION)

    # The following link appears in the database docker file. Its the same jdbc link as before
    mysql_jdbc = guacamole_jdbc

    if not url_exists(tomcat):
        sucess = False
        print('[ERROR] There is some issue with the link {}. Follow these steps to resolve it.\n'.format(tomcat) +
              '1. Go to the following link {} in your browser.\n'.format(
                  'https://www-us.apache.org/dist/tomcat/tomcat-8/') + '2. Check for the folder name with a tomcat ' +
              'version greater than ' + settings.TOMCAT_VERSION + '3. Use the new version name as the value for the variable TOMCAT_VERSION in the file '+ base_directory + '/guac_settings.py')




def run_tests():
    directories = settings.fetch_file_directories()
    check_directories_files(directories)
    check_dockerfile_links(directories[settings.DIRECTORY_BASE])
    print("All tests are complete and were successful")


if __name__ == '__main__':
    run_tests()
