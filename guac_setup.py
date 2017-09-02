#!/usr/bin/env python2.7

import os
import subprocess
import sys
from time import sleep

from guac_test import run_tests
from db.add_user import add_user
from db.add_user import fetch_new_usernames


SQL_CONTAINER_NAME = 'sql_container'
GUACAMOLE_CONTAINER_NAME = 'guacamole_container'
SQL_IMAGE_NAME = 'sql_image'
GUACAMOLE_IMAGE_NAME = 'guacamole_image'


# Creates the initial directory structure
def create_directory_structure():
    file_directory = os.path.dirname(os.path.realpath(__file__))

    if not os.path.isfile(file_directory + '/guac_test.py'):
        print("Error. guac_test.py is missing in the " + file_directory + " directory. Exiting application")
        sys.exit()

    if not os.path.exists(file_directory + '/generated_files/'):
        os.makedirs(file_directory + '/generated_files/')


# Cleans up after the code finishes executing
def clean_directory_structure():
    file_directory = os.path.dirname(os.path.realpath(__file__))

    if os.path.isfile(file_directory + '/db/__init__.pyc'):
        os.remove(file_directory + '/db/__init__.pyc')

    if os.path.isfile(file_directory + '/db/add_user.pyc'):
        os.remove(file_directory + '/db/add_user.pyc')

    if os.path.isfile(file_directory + '/guac_test.pyc'):
        os.remove(file_directory + '/guac_test.pyc')


def generate_passwords():
    mysql_root_password = subprocess.check_output(["openssl", "rand", "-hex", "18"]).strip()
    mysql_user_password = subprocess.check_output(["openssl", "rand", "-hex", "18"]).strip()
    file_directory = os.path.dirname(os.path.realpath(__file__))
    with open(file_directory + '/generated_files/root_pass','w') as file:
        file.write(mysql_root_password)

    os.chmod(file_directory + '/generated_files/root_pass',0o600)

    with open(file_directory + '/generated_files/user_pass','w') as file:
        file.write(mysql_user_password)

    os.chmod(file_directory + '/generated_files/user_pass', 0o600)

    return mysql_root_password,mysql_user_password


# Generates guacamole.properties file
def generate_guac_file(mysql_user_password):
    file_directory = os.path.dirname(os.path.realpath(__file__))
    with open(file_directory + '/dock/guacamole.properties','w') as file:
        # Values for guacd
        guacd_values = 'guacd-hostname: localhost\n' + \
                       'guacd-port: 4822\n'
        # values for CAS module
        cas_values = 'cas-authorization-endpoint: https://cas.iu.edu/cas\n' + \
                     'cas-redirect-uri: http://poc1.dyndns-at-work.com:8080/guacamole\n'
        mysql_host = 'mysql-hostname: '+ SQL_CONTAINER_NAME + '\n'
        mysql_port = 'mysql-port: 3306\n'
        mysql_database = 'mysql-database: guacamole_db\n'
        mysql_username = 'mysql-username: guacamole_user\n'
        mysql_password = 'mysql-password: ' + mysql_user_password +'\n'
        # Values for MYSQL Authentication
        mysql_values = mysql_host + mysql_port + mysql_database + mysql_username + mysql_password

        file.write(guacd_values + cas_values + mysql_values)

    os.chmod(file_directory + '/generated_files/guacamole.properties', 0o600)


# Removes the guacamole container and sql container if they exist
def remove_containers():
    sql_container_name = SQL_CONTAINER_NAME
    guacamole_contatiner_name = GUACAMOLE_CONTAINER_NAME
    # Remove all running/stopped containers
    sql_container_id = subprocess.check_output(["docker", "ps", "--all", "--quiet", "--filter", "name="+sql_container_name]).strip()
    guacamole_container_id = subprocess.check_output(["docker", "ps", "--all", "--quiet", "--filter", "name="+guacamole_contatiner_name]).strip()

    if len(sql_container_id)>0:
        print("Removing the SQL container of the name {}".format(sql_container_name))
        subprocess.check_output(["docker", "rm", "-f", sql_container_id])

    if len(guacamole_container_id)>0:
        print("Removing the Guacamole container of the name {}".format(guacamole_contatiner_name))
        subprocess.check_output(["docker", "rm", "-f", guacamole_container_id])


def remove_images():

    sql_image_name = SQL_IMAGE_NAME
    guacamole_image_name = GUACAMOLE_IMAGE_NAME
    sql_image_id = subprocess.check_output(["docker", "images", "--quiet", sql_image_name]).strip()
    guacamole_image_id = subprocess.check_output(["docker", "images", "--quiet", guacamole_image_name]).strip()

    if len(sql_image_id)>0:
        print("Removing the SQL Image of the name {}".format(sql_image_name))
        subprocess.check_output(["docker", "rmi", sql_image_name])

    if len(guacamole_image_id)>0:
        print("Removing the Guacamole image of the name {}".format(guacamole_image_name))
        subprocess.check_output(["docker", "rmi", guacamole_image_name])

def build_sql_image():
    sql_image_name = SQL_IMAGE_NAME
    print("Building the SQL image...")
    subprocess.call(["docker","build","-t",sql_image_name,"./db/."])
    print("SQL image successfully built!")


def build_sql_container(mysql_root_password,mysql_user_password):
    sql_container_name = SQL_CONTAINER_NAME
    sql_image_name = SQL_IMAGE_NAME
    print("Creating the SQL container")
    subprocess.call(["docker", "run", "--name", sql_container_name,
                     "-e","MYSQL_ROOT_PASSWORD=" + mysql_root_password,
                     "-d", sql_image_name])
    print("Waiting for 30 seconds to setup SQL container with Guacamole Scripts")
    sleep(30)

    # Run the initialization scripts for the database
    subprocess.call(["docker", "exec", "-it", sql_container_name, "bash",
                     "/docker-entrypoint-initdb.d/db_init_scripts.sh",
                     mysql_root_password, mysql_user_password])
    print("SQL Container successfully created!")


def build_guacamole_image():
    guacamole_image_name = GUACAMOLE_IMAGE_NAME
    print("Building the Guacamole Image")
    subprocess.call(["docker", "build", "-t", guacamole_image_name, "./dock/."])
    print("Guacamole image successfully built")


def build_guacamole_container():
    sql_container_name = SQL_CONTAINER_NAME
    guacamole_container_name = GUACAMOLE_CONTAINER_NAME
    guacamole_image_name = GUACAMOLE_IMAGE_NAME
    print("Creating the Guacamole Container and linking to the SQL container")
    subprocess.call(["docker", "run", "--name", guacamole_container_name,
                     "--link", sql_container_name, "-p", "8080:8080",
                     "-it", guacamole_image_name])
    print("Guacamole container successfully created and linked to SQL Container")


def main():
    run_tests()
    create_directory_structure()
    mysql_root_password, mysql_user_password = generate_passwords()
    remove_containers()
    remove_images()
    build_sql_image()
    build_sql_container(mysql_root_password, mysql_user_password)
    usernames = fetch_new_usernames()
    add_user(usernames, SQL_CONTAINER_NAME, mysql_user_password)
    generate_guac_file(mysql_user_password)
    build_guacamole_image()
    build_guacamole_container()
    clean_directory_structure()

if __name__ == '__main__':
    main()