#!/usr/bin/env python2.7

import os
import subprocess
import sys
from time import sleep

from guac_test import run_tests
import guac_settings as settings


# Creates the initial directory structure
def create_directory_structure(directories):

    if not os.path.isfile(directories[settings.DIRECTORY_BASE] + '/guac_test.py'):
        print((
            "Error. guac_test.py is missing in the {} directory. "
            "Exiting application").format(directories[settings.DIRECTORY_BASE]))
        sys.exit()

    if not os.path.exists(directories[settings.DIRECTORY_BASE] + '/generated_files/'):
        os.makedirs(directories[settings.DIRECTORY_BASE] + '/generated_files/')


# Cleans up after the code finishes executing
def clean_directory_structure(directories):

    if os.path.isfile(directories[settings.DIRECTORY_BASE] + '/guac_test.pyc'):
        os.remove(directories[settings.DIRECTORY_BASE] + '/guac_test.pyc')

    if os.path.isfile(directories[settings.DIRECTORY_BASE] + '/guac_settings.pyc'):
        os.remove(directories[settings.DIRECTORY_BASE] + '/guac_settings.pyc')


# Fetches the IU username which acts as the Guacamole Administrator
# Todo: Can cause SQL injection. Need to sanitize input. Minimal risk here though.
def fetch_administrator(directories):
    usernames = []

    print('Fetching the usernames in the {}'.format(settings.FILE_NAME))

    with open(directories[settings.DIRECTORY_DATABASE]+'/' + settings.FILE_NAME) as file:
        for line in file:
            if line.strip()[0] != '#':
                usernames.append(line.strip())

    if len(usernames) is not 1:
        print("Error. Only one IU username allowed in the administrator file")
        sys.exit()

    return usernames[0]

def generate_passwords(directories):
    mysql_root_password = subprocess.check_output(["openssl", "rand", "-hex", "18"]).strip()
    mysql_user_password = subprocess.check_output(["openssl", "rand", "-hex", "18"]).strip()

    with open(directories[settings.DIRECTORY_BASE] + '/generated_files/root_pass','w') as file:
        file.write(mysql_root_password)

    os.chmod(directories[settings.DIRECTORY_BASE] + '/generated_files/root_pass',0o600)

    with open(directories[settings.DIRECTORY_BASE] + '/generated_files/user_pass','w') as file:
        file.write(mysql_user_password)

    os.chmod(directories[settings.DIRECTORY_BASE] + '/generated_files/user_pass', 0o600)

    return mysql_root_password, mysql_user_password


# Generates guacamole.properties file
def generate_guac_properties(mysql_user_password, directories):

    with open(directories[settings.DIRECTORY_GUACAMOLE] + '/guacamole.properties','w') as file:
        # Values for guacd
        guacd_values = 'guacd-hostname: localhost\n' + \
                       'guacd-port: 4822\n'
        # values for CAS module
        cas_values = 'cas-authorization-endpoint: https://cas.iu.edu/cas\n' + \
                     'cas-redirect-uri: http://poc1.dyndns-at-work.com:8080/guacamole\n'
        mysql_host = 'mysql-hostname: '+ settings.SQL_CONTAINER_NAME + '\n'
        mysql_port = 'mysql-port: 3306\n'
        mysql_database = 'mysql-database: guacamole_db\n'
        mysql_username = 'mysql-username: guacamole_user\n'
        mysql_password = 'mysql-password: ' + mysql_user_password +'\n'
        # Values for MYSQL Authentication
        mysql_values = mysql_host + mysql_port + mysql_database + mysql_username + mysql_password

        file.write(guacd_values + cas_values + mysql_values)

    os.chmod(directories[settings.DIRECTORY_GUACAMOLE] + '/guacamole.properties', 0o600)


# Removes the guacamole container and sql container if they exist
def remove_containers():
    # Remove all running/stopped containers
    sql_container_id = subprocess.check_output(["docker", "ps", "--all", "--quiet",
                                                "--filter", "name="+settings.SQL_CONTAINER_NAME]).strip()
    guacamole_container_id = subprocess.check_output(["docker", "ps", "--all", "--quiet",
                                                      "--filter", "name=" + settings.GUACAMOLE_CONTAINER_NAME]).strip()

    if len(sql_container_id)>0:
        print("Removing the SQL container of the name {}".format(settings.SQL_CONTAINER_NAME))
        subprocess.check_output(["docker", "rm", "-f", sql_container_id])

    if len(guacamole_container_id)>0:
        print("Removing the Guacamole container of the name {}".format(settings.GUACAMOLE_CONTAINER_NAME))
        subprocess.check_output(["docker", "rm", "-f", guacamole_container_id])


def remove_images():
    sql_image_id = subprocess.check_output(["docker", "images", "--quiet", settings.SQL_IMAGE_NAME]).strip()
    guacamole_image_id = subprocess.check_output(["docker", "images", "--quiet", settings.GUACAMOLE_IMAGE_NAME]).strip()

    if len(sql_image_id)>0:
        print("Removing the SQL Image of the name {}".format(settings.SQL_IMAGE_NAME))
        subprocess.check_output(["docker", "rmi", settings.SQL_IMAGE_NAME])

    if len(guacamole_image_id)>0:
        print("Removing the Guacamole image of the name {}".format(settings.GUACAMOLE_IMAGE_NAME))
        subprocess.check_output(["docker", "rmi", settings.GUACAMOLE_IMAGE_NAME])

def build_sql_image(directories):
    print("Building the SQL image...")
    subprocess.call(["docker", "build", '--build-arg', 'GUACAMOLE_VERSION={}'.format(settings.GUACAMOLE_VERSION),
                     "-t",settings.SQL_IMAGE_NAME, directories[settings.DIRECTORY_DATABASE] + '/.'])
    print("SQL image successfully built!")


def build_sql_container(mysql_root_password,mysql_user_password,administrator):
    print("Creating the SQL container")
    subprocess.call(["docker", "run", "--name", settings.SQL_CONTAINER_NAME,
                     "-e", "MYSQL_ROOT_PASSWORD=" + mysql_root_password,
                     "-d", settings.SQL_IMAGE_NAME])
    print("Waiting for 30 seconds to setup SQL container with Guacamole Scripts")
    sleep(30)

    # Run the initialization scripts for the database
    subprocess.call(["docker", "exec", "-it", settings.SQL_CONTAINER_NAME, "bash",
                     "/docker-entrypoint-initdb.d/db_init_scripts.sh",
                     mysql_root_password, mysql_user_password, administrator])
    print("SQL Container successfully created!")


def build_guacamole_image(directories):
    print("Building the Guacamole Image")
    subprocess.call(["docker", "build", '--build-arg', 'GUACAMOLE_VERSION=' + settings.GUACAMOLE_VERSION,
                     '--build-arg', 'TOMCAT_VERSION=' + settings.TOMCAT_VERSION,
                     '--build-arg', 'MYSQL_CONNECTOR_VERSION=' + settings.MYSQL_CONNECTOR_VERSION,
                     "-t", settings.GUACAMOLE_IMAGE_NAME,
                     directories[settings.DIRECTORY_GUACAMOLE] + '/.'])
    print("Guacamole image successfully built")


def build_guacamole_container():
    print("Creating the Guacamole Container and linking to the SQL container")
    subprocess.call(["docker", "run", "--name", settings.GUACAMOLE_CONTAINER_NAME,
                     "--link", settings.SQL_CONTAINER_NAME, "-p", "8080:8080",
                     "-d", "-t", settings.GUACAMOLE_IMAGE_NAME])
    print("Guacamole container successfully created and linked to SQL Container")


def main():
    run_tests()
    directories = settings.fetch_file_directories()
    create_directory_structure(directories)
    administrator = fetch_administrator(directories)
    mysql_root_password, mysql_user_password = generate_passwords(directories)
    remove_containers()
    remove_images()
    generate_guac_properties(mysql_user_password, directories)
    build_sql_image(directories)
    build_sql_container(mysql_root_password, mysql_user_password, administrator)
    build_guacamole_image(directories)
    build_guacamole_container()
    clean_directory_structure(directories)

if __name__ == '__main__':
    main()
