#!/usr/bin/env python3


import os
import subprocess
import sys


def add_dependencies():
    print("Adding dependencies")
    # Get the source to download perfsonar if one not present already
    if not os.path.isfile('/etc/apt/sources.list.d/perfsonar-jessie-release.list'):
        try:
            subprocess.check_output(['wget', '-P', '/etc/apt/sources.list.d/',
                                     'http://downloads.perfsonar.net/debian/perfsonar-jessie-release.list'])
        except subprocess.CalledProcessError as err:
            print("[Error] Error adding source. Cannot continue with perfsonar installation please install it manually")
            print(err)

    else:
        print("Source already present..skipping this step..")

    # Add key
    try:
        subprocess.check_call(
            ['wget -qO - http://downloads.perfsonar.net/debian/perfsonar-debian-official.gpg.key | apt-key add -'],
            shell=True)
    except subprocess.CalledProcessError as err:
        print("[Error] Cannot add key. Aborting perfsonar installation. Please install it manually")
        print(err)
        sys.exit()

    print("Updating apt")

    # Updating apt
    try:
        subprocess.check_call(['apt-get', '-y', 'update'])
    except subprocess.CalledProcessError as err:
        print("[Error] apt update failed. Aborting installation. Please install perfsonar manually")
        print(err)
        sys.exit()


def install_perfsonar_testpoint():
    print("installing perfsonar testpoint")

    try:
        # Install from source added above
        subprocess.call('sudo apt-get install --no-install-recommends perfsonar-testpoint -y', shell=True)
    except subprocess.CalledProcessError as err:
        print("[Error] Installation failed. Please install it manually")
        print(err)
        sys.exit()


def install_additional_packages():
    packages = ['perfsonar-toolkit-ntp',
                'perfsonar-toolkit-security',
                'perfsonar-toolkit-servicewatcher',
                'perfsonar-toolkit-sysctl',
                'perfsonar-toolkit-systemenv-testpoint']

    print('Installing the following packages {}'.format(", ".join(packages)))
    try:
        subprocess.check_call(['sudo', 'DEBIAN_FRONTEND=noninteractive', 'apt-get', '-y', 'install'] + packages)

    except subprocess.CalledProcessError as err:
        print("[Error] Cannot install additional packages. Please install them manually")
        print(err)
        sys.exit()


def setup_perfsonar():
    # Call all the required functions
    add_dependencies()
    install_perfsonar_testpoint()
    install_additional_packages()


if __name__ == '__main__':
    setup_perfsonar()
