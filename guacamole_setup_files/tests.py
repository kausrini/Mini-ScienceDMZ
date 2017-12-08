#!/usr/bin/env python3

import os
import subprocess
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

    if not os.path.isfile(directories[settings.DIRECTORY_DATABASE] + '/ip_update.sh'):
        print('Error, the ip_update.sh file is missing from the db folder')
        success = False

    if not success:
        print("Fix the issues and re-run the application")
        sys.exit()

    print("[Success] All required files are present")


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
def check_dockerfile_links():
    success = True
    # Following links are present in the guacamole Dockerfile
    # The guacamole_jdbc link exists in both guacamole Dockerfile and database Dockerfile

    tomcat = (
        "https://www-us.apache.org/dist/tomcat/tomcat-8/v{}"
        "/bin/apache-tomcat-{}"
        ".tar.gz"
    ).format(settings.TOMCAT_VERSION, settings.TOMCAT_VERSION)

    guacamole_server = (
        'http://apache.mirrors.tds.net/guacamole/{}' 
        '-incubating/source/guacamole-server-{}' 
        '-incubating.tar.gz'
    ).format(settings.GUACAMOLE_VERSION,settings.GUACAMOLE_VERSION)

    guacamole_client = (
        'http://apache.mirrors.tds.net/guacamole/{}'
        '-incubating/binary/guacamole-{}-incubating.war'
    ).format(settings.GUACAMOLE_VERSION, settings.GUACAMOLE_VERSION)

    guacamole_cas = (
        'http://apache.mirrors.tds.net/guacamole/{}'
        '-incubating/binary/guacamole-auth-cas-{}-incubating.tar.gz'
    ).format(settings.GUACAMOLE_VERSION, settings.GUACAMOLE_VERSION)

    mysql_connector = (
        'https://cdn.mysql.com//Downloads/Connector-J/mysql-connector-java-{}.tar.gz'
    ).format(settings.MYSQL_CONNECTOR_VERSION)

    guacamole_jdbc = (
        'http://apache.mirrors.lucidnetworks.net/guacamole/{}'
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
        print('[Success] All links specified in the Dockerfiles are valid')


# Checks if the windows system is connected to our PI and RDP port is open
def check_rdp_connection():
    print("Checking if the equipment is connected to raspberry Pi and RDP is enabled")
    try:
        with open('/var/lib/dhcp/dhcpd.leases', 'r') as file:
            dhcpd_leases = file.read().strip()
    except FileNotFoundError as error:
        print("[Error] DNSmasq lease file not created yet. No leases issued yet? "
              "\nCheck DNSmasq and if equipment connected")
        sys.exit()

    ip_address_list = []

    for line in dhcpd_leases.split('\n'):
        if 'lease ' in line and ' {' in line:
            ip_address = line[line.find('lease ') + 6: line.find(' {')]
            if ip_address not in ip_address_list:
                ip_address_list.append(ip_address)

    if not ip_address_list:
        print("[Error] No lease Issued by dhcp server."
              "\nCheck dhcp server and if the equipment is connected")
        sys.exit()

    nmap_call_arguments = ['nmap', '-Pn'] + ip_address_list + ['-p', '3389', '--open']
    nmap_output = subprocess.check_output(nmap_call_arguments).decode("utf-8").strip()

    if '3389/tcp open  ms-wbt-server' not in nmap_output:
        print("[Error] RDP enabled device not connected to raspberry pi. "
              "\nRDP may not be enabled or the equipment might not be connected."
              "\nResolve issue and retry again")
        sys.exit()

    print("[Success] Equipment is connected to raspberry pi and RDP is enabled.")


# Checks if valid domain name entered in settings.py file
def check_domain_name(domain_name):
    if not len(domain_name):
        print('[ERROR] Valid DOMAIN_NAME missing from settings.py file'
              'Modify the value and re-run the script')
        sys.exit()


def run_tests():
    directories = settings.fetch_file_directories()
    check_directories_files(directories)
    check_domain_name(settings.DOMAIN_NAME)
    check_dockerfile_links()
    check_rdp_connection()
    print("All tests are complete and were successful")


if __name__ == '__main__':
    run_tests()
