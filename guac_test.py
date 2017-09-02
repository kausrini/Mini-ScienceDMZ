#!/usr/bin/env python2.7

import os


def check_directories_files():

    print("Checking if all the required files exist")

    file_directory = os.path.dirname(os.path.realpath(__file__))
    success = True

    if not os.path.exists(file_directory + '/db') or not os.path.exists(file_directory + '/dock'):
        print("Error. The folder " + file_directory + '/db is missing')
        success = False

    if not os.path.exists(file_directory + '/dock'):
        print("Error. The folder " + file_directory + '/dock is missing')
        success = False

    if not os.path.isfile(file_directory + '/dock/Dockerfile'):
        print('Error, the setup.sh file is missing from the dock folder')
        success = False

    if not os.path.isfile(file_directory + '/db/Dockerfile'):
        print('Error, the Dockerfile is missing from the db folder')
        success = False

    if not os.path.isfile(file_directory + '/db/db_init_scripts.sh'):
        print('Error, the db_init_scripts.sh file is missing from the db folder')
        success = False

    if not os.path.isfile(file_directory + '/db/users.txt'):
        print('Error, the users.txt file is missing from the db folder. ' +
              'It needs to contain the user list to access the guacamole connection')
        success = False

    if not os.path.isfile(file_directory + '/db/add_user.py'):
        print('Error, the add_user.py file is missing from the db folder')
        success = False

    if not success:
        print("Fix the issues and re-run the application")
        sys.exit()

    print("All required files are present")

# Todo: Do this (Need to pass guacamole Environment variable)
def check_dockerfile_links():
    print("TO DO")

def run_tests():
    check_directories_files()
    print("All tests are complete and were successful")

if __name__ == '__main__':
    run_tests()