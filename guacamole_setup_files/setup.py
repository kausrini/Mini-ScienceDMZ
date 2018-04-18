#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
from time import sleep

from tests import run_tests
import settings

DOCKER_MYSQL_VOLUME = 'sql_volume'


# Obtain command line arguments
def fetch_argument():
    parser = argparse.ArgumentParser(description='Sets up the Guacamole Server')

    parser.add_argument('-f', '--force',
                        help='Forces creation of new instance of application. Removes old data.',
                        action='store_true'
                        )

    parser.add_argument('-u', '--username',
                        help='The CAS username which acts as the Administrator for the Guacamole application',
                        required=True
                        )
    arguments = parser.parse_args()
    return arguments


def user_prompt(prompt_message):
    while True:
        sys.stdout.write(prompt_message + '? [y/n] ')

        valid_choices = {"yes": True, "y": True, "ye": True,
                         "no": False, "n": False}

        choice = input().lower()

        if choice in valid_choices:
            break
        else:
            print("Please respond with 'yes' or 'no' (or 'y' or 'n').")

    return valid_choices[choice]


# Creates the initial directory structure
def create_directory_structure(directories):
    if not os.path.isfile(directories[settings.DIRECTORY_BASE] + '/tests.py'):
        print((
                  "[Error] tests.py is missing in the {} directory. "
                  "Exiting application"
              ).format(directories[settings.DIRECTORY_BASE]))
        sys.exit()

    if not os.path.exists(directories[settings.DIRECTORY_GENERATED_FILES]):
        os.makedirs(directories[settings.DIRECTORY_GENERATED_FILES])


# Cleans up after the code finishes executing
def clean_directory_structure(directories):
    if os.path.isfile(directories[settings.DIRECTORY_BASE] + '/tests.pyc'):
        os.remove(directories[settings.DIRECTORY_BASE] + '/tests.pyc')

    if os.path.isfile(directories[settings.DIRECTORY_BASE] + '/settings.pyc'):
        os.remove(directories[settings.DIRECTORY_BASE] + '/settings.pyc')


# A function which uses the openssl package in the operating system to generate mysql passwords
def generate_passwords(generate, directories):
    if not generate:
        with open(directories[settings.DIRECTORY_GENERATED_FILES] + '/mysql_root_pass', 'r') as file_object:
            mysql_root_password = file_object.read()
        with open(directories[settings.DIRECTORY_GENERATED_FILES] + '/mysql_user_pass', 'r') as file_object:
            mysql_user_password = file_object.read()
    else:
        mysql_root_password = subprocess.check_output(["openssl", "rand", "-hex", "18"]).decode("utf-8").strip()
        mysql_user_password = subprocess.check_output(["openssl", "rand", "-hex", "18"]).decode("utf-8").strip()
        with open(directories[settings.DIRECTORY_GENERATED_FILES] + '/mysql_root_pass', 'w') as file_object:
            file_object.write(mysql_root_password)
        os.chmod(directories[settings.DIRECTORY_GENERATED_FILES] + '/mysql_root_pass', 0o660)
        with open(directories[settings.DIRECTORY_GENERATED_FILES] + '/mysql_user_pass', 'w') as file_object:
            file_object.write(mysql_user_password)
        os.chmod(directories[settings.DIRECTORY_GENERATED_FILES] + '/mysql_user_pass', 0o660)

    return mysql_root_password, mysql_user_password


# Generates guacamole.properties file
def generate_guac_properties(mysql_user_password, directories):
    with open(directories[settings.DIRECTORY_GUACAMOLE] + '/guacamole.properties', 'w') as file_object:
        # Values for guacd
        guacd_values = (
            'guacd-hostname: localhost\n'
            'guacd-port: 4822\n'
        )
        mysql_host = 'mysql-hostname: {}\n'.format(settings.SQL_CONTAINER_NAME)
        mysql_port = 'mysql-port: 3306\n'
        mysql_database = 'mysql-database: guacamole_db\n'
        mysql_username = 'mysql-username: guacamole_user\n'
        mysql_password = 'mysql-password: {}\n'.format(mysql_user_password)
        # Values for MYSQL Authentication
        mysql_values = mysql_host + mysql_port + mysql_database + mysql_username + mysql_password

        file_object.write(guacd_values + mysql_values)

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


# Returns a list of ip addresses connected to the raspberry pi with rdp enabled.
# If none detected, returns empty list
def fetch_equipment_ip():
    print('Fetching equipment IP address')

    # Using a list of ip address for a future case where single raspberry pi is connected to
    # multiple rdp enabled devices. Obviously return the entire list insted of list[0] for
    # such a case.
    ip_address_list = []

    try:
        with open('/var/lib/dhcp/dhcpd.leases', 'r') as file_object:
            dhcpd_leases = file_object.read().strip()
    except FileNotFoundError as error:
        print("[Error] dhcp lease file {} not created yet. No leases issued yet! "
              "\nCheck if dhcpd and if equipment connected")
        return ip_address_list

    # Fetch list of ip addresses from dhcp lease
    for line in dhcpd_leases.split('\n'):
        if 'lease ' in line and ' {' in line:
            ip_lease_address = line[line.find('lease ') + 6: line.find(' {')]
            if ip_lease_address not in ip_address_list:
                ip_address_list.append(ip_lease_address)

    if not ip_address_list:
        print("[ERROR] No lease Issued by dhcpd."
              "\nCheck dhcpd  and if the equipment is connected")
        return ip_address_list

    # Port scan dhcp addresses present in the dhcpd lease file for RDP device
    nmap_call_arguments = ['nmap', '-Pn'] + ip_address_list + ['-p', '3389', '--open']
    nmap_output = subprocess.check_output(nmap_call_arguments).decode("utf-8").strip()

    # Ip address list of RDP enabled devices
    rdp_enabled_devices = None
    if '3389/tcp open  ms-wbt-server' not in nmap_output:
        print("[ERROR] RDP enabled device not connected to raspberry pi.")
    else:
        nmap_second_line = nmap_output.split("\n")[1].strip()
        rdp_enabled_devices = nmap_second_line.split(' ')[-1:]

    if not rdp_enabled_devices:
        print('[ERROR] The device connected to the raspberry pi does not have RDP enabled')
    else:
        print('Successful extraction of equipment ip address')

    return rdp_enabled_devices


# Builds the sql container from the sql image
def build_sql_container(docker_network_name, mysql_root_password, mysql_user_password, administrator, new_database):

    ip_address_list = fetch_equipment_ip()

    ip_address = "192.168.7.2"

    if ip_address_list:
        # Assuming only one device connected to our raspberry pi for now
        # In future loop through this list and setup multiple equipments connected
        # to the raspberry pi.
        ip_address = ip_address_list[0]
        user_choice = True
    else:
        user_choice = user_prompt("There were no valid ip addresses detected for the equipment connected to "
                                  "the raspberry pi. \nIf you continue the setup, you might need to manually "
                                  "update the ip address using the script provided.\n"
                                  "Would you like to continue the setup")

    if not user_choice:
        sys.exit()

    print('Configuring the ip address {} for the equipment'.format(ip_address))

    if new_database:
        print('Creating docker volume {} for mysql'.format(DOCKER_MYSQL_VOLUME))
        subprocess.check_output(['docker', 'volume', 'create', DOCKER_MYSQL_VOLUME])

    print("Creating the SQL container")
    call_arguments = ["docker", "run", "--network={}".format(docker_network_name),
                      "--name", settings.SQL_CONTAINER_NAME,
                      "-v", "{}:/var/lib/mysql".format(DOCKER_MYSQL_VOLUME)
                      ]

    # Need to send MYSQL Root Password if container created for the first time.
    if new_database:
        call_arguments = call_arguments + ["-e", "MYSQL_ROOT_PASSWORD={}".format(mysql_root_password)]

    call_arguments = call_arguments + ["-d", settings.SQL_IMAGE_NAME]

    subprocess.call(call_arguments)

    print("Waiting for 30 seconds to setup SQL container with Guacamole Scripts")
    sleep(30)

    # Need to update ip address of equipment to be sure
    if not new_database:
        print("Updating IP address of the equipment")
        subprocess.call(["docker", "exec", "-it", settings.SQL_CONTAINER_NAME, "bash",
                         "/docker-entrypoint-initdb.d/ip_update.sh", mysql_user_password, ip_address])
        print("SQL Container successfully created!")
        return

    # Run the initialization scripts for the database
    subprocess.call(["docker", "exec", "-it", settings.SQL_CONTAINER_NAME, "bash",
                     "/docker-entrypoint-initdb.d/db_init_scripts.sh",
                     mysql_root_password, mysql_user_password, administrator, ip_address])
    print("SQL Container successfully created!")


# Builds the guacamole image
def build_guacamole_image(directories):
    print("Building the Guacamole Image")
    subprocess.call(["docker", "build", '--build-arg', 'GUACAMOLE_VERSION=' + settings.GUACAMOLE_VERSION,
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


# Method checks if the docker volume for mysql exists
def mysql_volume_exists():
    existing_volumes = subprocess.check_output(['docker', 'volume', 'ls', '-q']).decode("utf-8")
    if DOCKER_MYSQL_VOLUME in existing_volumes:
        print('Mysql will be mounted on the existing docker volume {}'.format(DOCKER_MYSQL_VOLUME))
        return True

    return False


# Checks if previous instances of sql passwords exist
def sql_passwords_exist(directories):
    if os.path.isfile(directories[settings.DIRECTORY_GENERATED_FILES] + '/mysql_root_pass') and os.path.isfile(
                    directories[settings.DIRECTORY_GENERATED_FILES] + '/mysql_user_pass'):
        return True
    return False


def new_sql_database(directories, reset_database):
    if mysql_volume_exists():
        if sql_passwords_exist(directories) and not reset_database:
            print('Existing User configuration detected. The administrator provided will be discarded')
            return False
        subprocess.check_output(['docker', 'volume', 'rm', DOCKER_MYSQL_VOLUME])

    return True


def main():
    directories = settings.fetch_file_directories()
    create_directory_structure(directories)
    arguments = fetch_argument()
    administrator = arguments.username
    force = arguments.force
    run_tests()
    remove_containers()
    remove_images()
    new_database = new_sql_database(directories, force)
    mysql_root_password, mysql_user_password = generate_passwords(new_database, directories)
    generate_guac_properties(mysql_user_password, directories)
    docker_network_name = create_docker_network()
    build_sql_image(directories)
    build_sql_container(docker_network_name, mysql_root_password, mysql_user_password, administrator, new_database)
    build_guacamole_image(directories)
    build_guacamole_container(docker_network_name)
    clean_directory_structure(directories)


if __name__ == '__main__':
    main()
