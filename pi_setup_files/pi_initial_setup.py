#!/usr/bin/env python3

import argparse
import getpass
import os
import shutil
import subprocess
import time
import sys

import pi_settings as settings


# Obtain absolute location of this python file
def file_directory():
    path = os.path.dirname(os.path.realpath(__file__))
    return path


# Obtain command line arguments
def fetch_argument():
    parser = argparse.ArgumentParser(description='Raspberry Pi setup part-1')

    parser.add_argument('-s', '--ssid',
                        help='Provide the Wireless network SSID',
                        required=True
                        )

    # WPA-EAP requires an username and password for connecting to the network. Typical enterprise config
    # WPA-PSK requires only a password (pre-shared key) for connecting to network. Typical home network

    while True:
        sys.stdout.write('Are you trying to connect to an Enterprise wifi network (WPA-EAP) which requires'
                         ' an username for connection? [Y/n] ')

        valid_choices = {"yes": True, "y": True, "ye": True,
                         "no": False, "n": False}

        choice = input().lower()

        if choice in valid_choices:
            break
        else:
            print("Please respond with 'yes' or 'no' (or 'y' or 'n').")

    wifi_username = None

    if valid_choices[choice]:
        parser.add_argument('-u', '--username',
                            help='Username to connect to the Wireless network',
                            required=True
                            )

    arguments = parser.parse_args()

    wifi_ssid = arguments.ssid

    if valid_choices[choice]:
        wifi_username = arguments.username

    while True:
        wifi_password = getpass.getpass('Enter Wifi Password : ')
        wifi_verify_password = getpass.getpass('Re-enter Wifi Password : ')

        if wifi_password == wifi_verify_password:
            break
        else:
            print("[Error] The passwords do not match. Please enter again.")

    return wifi_ssid, wifi_username, wifi_password


# Configurations directly modifying pi
def pi_configuration():
    # Pi for a headless application then you can reduce the memory split
    # between the GPU and the rest of the system down to 16mb
    print('Setting GPU memory to 16mb')
    config_file = '/boot/config.txt'
    config_file_backup = '/boot/config_backup.txt'
    try:
        if not os.path.isfile(config_file_backup):
            shutil.copy2(config_file, config_file_backup)
        else:
            shutil.copy2(config_file_backup, config_file)
    except OSError as error:
        if 'Permission denied' in error.strerror:
            print("[ERROR] Code is executed as a non privileged user."
                  "\n[ERROR] Please re-run the script as superuser. [ sudo ./{} ]".format(os.path.basename(__file__)))
            sys.exit()
        print('[ERROR] Unknown error occurred while accessing {} file'.format(config_file))
        print('[ERROR] {}'.format(error.strerror))
        sys.exit()

    with open(config_file, 'a') as file:
        file.write('gpu_mem=16')

    # Forcing user to change default pi password
    print('Please change the default Rapberry Pi password')
    while True:
        try:
            subprocess.check_output('passwd pi', shell=True)
        except subprocess.CalledProcessError:
            print("[ERROR] Please try again!")
            continue
        break

    # Creating a file called ssh in boot.
    # This is required to enable ssh connection to pi
    with open('/boot/ssh', 'w') as file:
        file.write('')

    # Changing default keyboard layout to 'US'
    subprocess.check_output(['sed', '-i', '--',
                             's|pc105|pc104|g',
                             '/etc/default/keyboard'])
    subprocess.check_output(['sed', '-i', '--',
                             's|gb|us|g',
                             '/etc/default/keyboard'])


# Create the firewall configuration for the raspberry pi
def firewall_configuration(base_path):
    print('Setting up the firewall configuration')
    firewall_path = '/etc/firewall'
    firewall_script_name = '/iptables.sh'

    # Creating the folder for our firewall script file
    try:
        os.makedirs(firewall_path)
    except OSError as error:
        if 'File exists' in error.strerror:
            print('{} directory already exists'.format(firewall_path))

    # copying iptables rules to the new folder
    shutil.copy2(base_path + firewall_script_name, firewall_path + firewall_script_name)

    # Changing file permissions
    os.chmod(firewall_path + firewall_script_name, 0o700)
    subprocess.check_output(['chown', 'root', firewall_path + firewall_script_name])


# Create the dynamic dns configuration for the raspberry pi
def dns_configuration(base_path):
    print('Setting up the dynamic dns configuration')
    file_name = '/dynv6.sh'
    path_name = '/etc/dns'

    # Creating the folder for our dns script file
    try:
        os.makedirs(path_name)
    except OSError as error:
        if 'File exists' in error.strerror:
            print('{} directory already exists'.format(path_name))

    # copying dns script to the new folder
    shutil.copy2(base_path + file_name, path_name + file_name)

    # Changing file permissions
    os.chmod(path_name + file_name, 0o700)
    subprocess.check_output(['chown', 'root', path_name + file_name])

    subprocess.check_output(['sed', '-i', '--',
                             's|token="YOUR_DYNV6_TOKEN_HERE"|token="' + settings.DYNV6_API_TOKEN + '"|g',
                             path_name + file_name])

    subprocess.check_output(['sed', '-i', '--',
                             's|hostname="YOUR_DOMAIN_NAME_HERE"|hostname="' + settings.DOMAIN_NAME + '"|g',
                             path_name + file_name])


# Create Wifi configuration for connecting to Wireless network
# Adds script to initialize firewall rules
# Adds script to register ip with dynv6 dynamic dns service
def network_configuration(wifi_ssid, wpa_username, wpa_password):
    print('Setting up the wifi configuration')

    wpa_config_file = '/etc/wpa_supplicant/wpa_supplicant.conf'
    wpa_config_backup = '/etc/wpa_supplicant/wpa_supplicant_backup.conf'
    interfaces_file = '/etc/network/interfaces'
    interfaces_backup = interfaces_file + '_backup'

    if wpa_username is not None:
        # WPA-EAP Configuration
        wpa_config = (
            '\tssid="{}"\n'
            '\tkey_mgmt=WPA-EAP\n'
            '\tpairwise=CCMP TKIP\n'
            '\tgroup=CCMP TKIP\n'
            '\teap=PEAP\n'
            '\tphase1="peapver=0"\n'
            '\tphase2="MSCHAPV2"\n'
            '\tidentity="{}"\n'
            '\tpassword="{}"\n'
        ).format(wifi_ssid, wpa_username, wpa_password)
    else:
        # WPA-PSK Configuration
        # Note this configuration has not been (and won't be) tested.
        wpa_config = (
            '\tssid="{}"\n'
            '\tpsk="{}"\n'
        ).format(wifi_ssid, wpa_password)

    final_wpa_config = '\nnetwork={\n' + wpa_config + '}\n'

    loopback_config = (
        '\nauto lo\n'
        'iface lo inet loopback\n'
    )

    wifi_config = (
        '\nauto wlan0\n'
        'allow-hotplug wlan0\n'
        'iface wlan0 inet dhcp\n'
        '\twpa-conf /etc/wpa_supplicant/wpa_supplicant.conf\n'
        '\tpre-up /bin/bash /etc/firewall/iptables.sh\n'
    )

    ethernet_config = (
        '\nauto eth0\n'
        'iface eth0 inet static\n'
        '\taddress 192.168.7.1\n'
        '\tnetmask 255.255.255.0\n'
        '\tnetwork 192.168.7.0'
    )

    print('Adding WPA configuration to {} file'.format(wpa_config_file))
    if not os.path.isfile(wpa_config_backup):
        shutil.copy2(wpa_config_file, wpa_config_backup)
    else:
        shutil.copy2(wpa_config_backup, wpa_config_file)
    with open(wpa_config_file, 'a') as file:
        file.write(final_wpa_config)

    print('Adding WIFI configuration to {} file'.format(interfaces_file))
    if not os.path.isfile(interfaces_backup):
        shutil.copy2(interfaces_file, interfaces_backup)
    else:
        shutil.copy2(interfaces_backup, interfaces_file)
    with open(interfaces_file, 'a') as file:
        file.write(loopback_config + wifi_config + ethernet_config)


# Rebooting the raspberry pi
def clean_up_setup():
    print('Rebooting the system in 5 seconds...')
    time.sleep(5)
    subprocess.check_output(['reboot', 'now'])


if __name__ == '__main__':
    settings.test_values()
    ssid, username, password = fetch_argument()
    base_directory = file_directory()
    pi_configuration()
    firewall_configuration(base_directory)
    network_configuration(ssid, username, password)
    dns_configuration(base_directory)
    clean_up_setup()
