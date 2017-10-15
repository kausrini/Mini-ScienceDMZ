#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
from time import sleep

from tests import run_tests
import settings


# Obtain command line arguments
def fetch_argument():
    parser = argparse.ArgumentParser(description='Sets up the Guacamole Server')
    parser.add_argument('-u', '--username',
                        help='The IU username which acts as the Administrator for the Guacamole application',
                        required=True
                        )
    arguments = parser.parse_args()
    return arguments.username


# Creates the initial directory structure
def create_directory_structure(directories):
    if not os.path.isfile(directories[settings.DIRECTORY_BASE] + '/tests.py'):
        print((
                  "[Error] tests.py is missing in the {} directory. "
                  "Exiting application"
              ).format(directories[settings.DIRECTORY_BASE]))
        sys.exit()

        # if not os.path.exists(directories[settings.DIRECTORY_BASE] + '/generated_files/'):
        #    os.makedirs(directories[settings.DIRECTORY_BASE] + '/generated_files/')


# Cleans up after the code finishes executing
def clean_directory_structure(directories):
    if os.path.isfile(directories[settings.DIRECTORY_BASE] + '/tests.pyc'):
        os.remove(directories[settings.DIRECTORY_BASE] + '/tests.pyc')

    if os.path.isfile(directories[settings.DIRECTORY_BASE] + '/settings.pyc'):
        os.remove(directories[settings.DIRECTORY_BASE] + '/settings.pyc')


# A function which uses the openssl package in the operating system to generate mysql passwords
def generate_passwords():
    mysql_root_password = subprocess.check_output(["openssl", "rand", "-hex", "18"]).strip()
    mysql_user_password = subprocess.check_output(["openssl", "rand", "-hex", "18"]).strip()

    return mysql_root_password.decode("utf-8"), mysql_user_password.decode("utf-8")


# Generates guacamole.properties file
def generate_guac_properties(mysql_user_password, directories):
    with open(directories[settings.DIRECTORY_GUACAMOLE] + '/guacamole.properties', 'w') as file:
        # Values for guacd
        guacd_values = (
            'guacd-hostname: localhost\n'
            'guacd-port: 4822\n'
        )
        # values for CAS authentication module
        cas_values = (
            'cas-authorization-endpoint: {}\n'
            'cas-redirect-uri: {}\n'
        ).format(settings.CAS_AUTHORIZATION_ENDPOINT, settings.CAS_REDIRECT_URI)
        mysql_host = 'mysql-hostname: {}\n'.format(settings.SQL_CONTAINER_NAME)
        mysql_port = 'mysql-port: 3306\n'
        mysql_database = 'mysql-database: guacamole_db\n'
        mysql_username = 'mysql-username: guacamole_user\n'
        mysql_password = 'mysql-password: {}\n'.format(mysql_user_password)
        # Values for MYSQL Authentication
        mysql_values = mysql_host + mysql_port + mysql_database + mysql_username + mysql_password

        file.write(guacd_values + cas_values + mysql_values)

    os.chmod(directories[settings.DIRECTORY_GUACAMOLE] + '/guacamole.properties', 0o600)


# Removes the guacamole container and sql container if they already exist
def remove_containers():
    # Remove all running/stopped containers
    sql_container_id = subprocess.check_output(["docker", "ps", "--all", "--quiet",
                                                "--filter", "name=" + settings.SQL_CONTAINER_NAME]).strip()
    guacamole_container_id = subprocess.check_output(["docker", "ps", "--all", "--quiet",
                                                      "--filter", "name=" + settings.GUACAMOLE_CONTAINER_NAME]).strip()

    if len(sql_container_id) > 0:
        print("Removing the SQL container of the name {}".format(settings.SQL_CONTAINER_NAME))
        subprocess.check_output(["docker", "rm", "-f", sql_container_id])

    if len(guacamole_container_id) > 0:
        print("Removing the Guacamole container of the name {}".format(settings.GUACAMOLE_CONTAINER_NAME))
        subprocess.check_output(["docker", "rm", "-f", guacamole_container_id])


# Removes the existing SQL image and Guacamole image
def remove_images():
    sql_image_id = subprocess.check_output(["docker", "images", "--quiet", settings.SQL_IMAGE_NAME]).strip()
    guacamole_image_id = subprocess.check_output(["docker", "images", "--quiet", settings.GUACAMOLE_IMAGE_NAME]).strip()

    if len(sql_image_id) > 0:
        print("Removing the SQL Image of the name {}".format(settings.SQL_IMAGE_NAME))
        subprocess.check_output(["docker", "rmi", settings.SQL_IMAGE_NAME])

    if len(guacamole_image_id) > 0:
        print("Removing the Guacamole image of the name {}".format(settings.GUACAMOLE_IMAGE_NAME))
        subprocess.check_output(["docker", "rmi", settings.GUACAMOLE_IMAGE_NAME])


# Builds the sql image
def build_sql_image(directories):
    print("Building the SQL image...")
    subprocess.call(["docker", "build", '--build-arg', 'GUACAMOLE_VERSION={}'.format(settings.GUACAMOLE_VERSION),
                     "-t", settings.SQL_IMAGE_NAME, directories[settings.DIRECTORY_DATABASE] + '/.'])
    print("SQL image successfully built!")


# Create a custom network for our containers
def create_docker_network():
    docker_network_name = 'guacamole_network'
    network_id = subprocess.check_output(['docker', 'network', 'ls', '--filter',
                                          'name={}'.format(docker_network_name), '-q']
                                         ).strip()

    if len(network_id) == 0:
        print('Creating a new docker network {} for our containers'.format(docker_network_name))
        subprocess.check_output(['docker', 'network', 'create', '--driver', 'bridge', docker_network_name])
    else:
        print("Containers will be created on the docker network {}".format(docker_network_name))

    return docker_network_name


# Builds the sql container from the sql image
def build_sql_container(docker_network_name, mysql_root_password, mysql_user_password, administrator):
    print("Creating the SQL container")
    subprocess.call(["docker", "run", "--network={}".format(docker_network_name), "--name", settings.SQL_CONTAINER_NAME,
                     "-e", "MYSQL_ROOT_PASSWORD={}".format(mysql_root_password),
                     "-d", settings.SQL_IMAGE_NAME])
    print("Waiting for 30 seconds to setup SQL container with Guacamole Scripts")
    sleep(30)

    # Run the initialization scripts for the database
    subprocess.call(["docker", "exec", "-it", settings.SQL_CONTAINER_NAME, "bash",
                     "/docker-entrypoint-initdb.d/db_init_scripts.sh",
                     mysql_root_password, mysql_user_password, administrator])
    print("SQL Container successfully created!")


# Builds the guacamole image
def build_guacamole_image(directories):
    print("Building the Guacamole Image")
    subprocess.call(["docker", "build", '--build-arg', 'GUACAMOLE_VERSION=' + settings.GUACAMOLE_VERSION,
                     '--build-arg', 'TOMCAT_VERSION=' + settings.TOMCAT_VERSION,
                     '--build-arg', 'MYSQL_CONNECTOR_VERSION=' + settings.MYSQL_CONNECTOR_VERSION,
                     "-t", settings.GUACAMOLE_IMAGE_NAME,
                     directories[settings.DIRECTORY_GUACAMOLE] + '/.'])
    print("Guacamole image successfully built")


# Builds the guacamole container from the guacamole image
def build_guacamole_container(docker_network_name):
    print("Creating the Guacamole Container and linking to the SQL container")
    subprocess.call(["docker", "run", "--network={}".format(docker_network_name),
                     "--name", settings.GUACAMOLE_CONTAINER_NAME,
                     "-p", "127.0.0.1:8080:8080",
                     "-d", "-t", settings.GUACAMOLE_IMAGE_NAME])

    print("Guacamole container successfully created and linked to SQL Container")


def main():
    administrator = fetch_argument()
    run_tests()
    directories = settings.fetch_file_directories()
    create_directory_structure(directories)
    mysql_root_password, mysql_user_password = generate_passwords()
    remove_containers()
    remove_images()
    generate_guac_properties(mysql_user_password, directories)
    docker_network_name = create_docker_network()
    build_sql_image(directories)
    build_sql_container(docker_network_name, mysql_root_password, mysql_user_password, administrator)
    build_guacamole_image(directories)
    build_guacamole_container(docker_network_name)
    clean_directory_structure(directories)


if __name__ == '__main__':
    main()
