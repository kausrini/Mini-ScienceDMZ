#!/usr/bin/env python2.7

import subprocess
import sys
import os

MYSQL_USERNAME = 'guacamole_user'
MYSQL_DATABASE = 'guacamole_db'
MYSQL_PORT = 3306
FILE_NAME = 'users.txt'
CONNECTION_NAME = 'RDP_Connection'

# Reads the sql data from guacamole.properties file
def read_sql_data():
    mysql_user_password = None
    sql_container_name = None
    data = None

    file_directory = os.path.dirname(os.path.realpath(__file__))

    try:
        with open(file_directory + '/../dock/guacamole.properties', 'r') as file:
            data = file.readlines()
    except IOError as e:
        print("Error reading the guacamole.properties file. Exiting application. The error is " + e.strerror)
        sys.exit()

    for line in data:
        temp_line = line.strip().split(':')
        if temp_line[0].strip() == 'mysql-hostname':
            sql_container_name = temp_line[1].strip()
        elif temp_line[0].strip() == 'mysql-password':
            mysql_user_password = temp_line[1].strip()

    if mysql_user_password is None or sql_container_name is None:
        print('[Error]. Mysql user password or sql container name missing in guacamole.properties file. Exiting application')
        sys.exit()

    return sql_container_name, mysql_user_password


def fetch_existing_usernames(sql_container_name, mysql_user_password):
    sql_query = "SELECT username FROM guacamole_user;"
    existing_usernames = subprocess.check_output(["docker", "exec", "-it",
                                                  sql_container_name, "mysql",
                                                  "-u", MYSQL_USERNAME,
                                                  "-p" + mysql_user_password,
                                                  MYSQL_DATABASE, "-Bse", sql_query])

    existing_usernames_dict = {}
    for username in existing_usernames.replace('\r\n', ' ').split():
        existing_usernames_dict[username] = ""

    return existing_usernames_dict


def fetch_new_usernames():
    file_name = FILE_NAME
    new_usernames = []
    file_directory = os.path.dirname(os.path.realpath(__file__))

    print('Fetching the usernames in the {}'.format(FILE_NAME))

    with open(file_directory + '/' + FILE_NAME) as file:
        for line in file:
            if line.strip()[0] != '#':
                new_usernames.append(line.strip())

    return new_usernames


def remove_duplicates(existing_usernames_dict, new_usernames):
    add_users = []
    for username in new_usernames:
        if username in existing_usernames_dict:
            print('The username {} already exists in the guacamole database'.format(username))
        else:
            add_users.append(username)

    return add_users


# Adds the usernames to guacamole user table and authorizes them to access the connection specified by CONNECTION_NAME
def add_user(usernames, sql_container_name, mysql_user_password):

    if len(usernames) == 0:
        print("No new user to be added")
        return

    print('Adding the following usernames to guacamole users and providing access to the connection\n{}'.format(usernames))
    connection_name = CONNECTION_NAME
    for username in usernames:

        add_user_query = "INSERT INTO guacamole_user(username,password_date) values ('{}',NOW());".format(username)

        user_conn_query = "INSERT INTO guacamole_connection_permission VALUES ((SELECT user_id FROM guacamole_user WHERE username='{}'), (SELECT connection_id FROM guacamole_connection WHERE connection_name = '{}' AND parent_id IS NULL), 'READ')".format(username,connection_name)

        subprocess.call(["docker", "exec", "-it",
                         sql_container_name, "mysql",
                         "-u", MYSQL_USERNAME,
                         "-p" + mysql_user_password,
                         MYSQL_DATABASE, "-Bse", add_user_query])

        subprocess.call(["docker", "exec", "-it",
                         sql_container_name, "mysql",
                         "-u", MYSQL_USERNAME,
                         "-p" + mysql_user_password,
                         MYSQL_DATABASE, "-Bse", user_conn_query])


def main():
    sql_container_name, mysql_user_password = read_sql_data()
    existing_usernames_dict = fetch_existing_usernames(sql_container_name, mysql_user_password)
    new_usernames = fetch_new_usernames()
    add_usernames = remove_duplicates(existing_usernames_dict,new_usernames)

    print('Existing usernames are {}'.format(existing_usernames_dict))
    print('New usernames are {}'.format(new_usernames))
    print('The usernames that will be added to the database are {}'.format(add_usernames))

    add_user(add_usernames, sql_container_name, mysql_user_password)

if __name__ == '__main__':
    main()
