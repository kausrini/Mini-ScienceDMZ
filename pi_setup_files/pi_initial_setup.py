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
    parser = argparse.ArgumentParser(description='Initial Pi Setup')

    parser.add_argument('-d', '--nodns',
                        help='Skip configuring dynamic dns. Users are expected to configure their domain name as they '
                             'see fit.',
                        action='store_true'
                        )

    parser.add_argument('-m', '--manual',
                        help='Script does not configure the network for internet connection for eth1. \n'
                             'User expected to configure the network themselves for eth1',
                        action='store_true'
                        )

    input_arguments = parser.parse_args()
    return input_arguments


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


# Check if wireless or wired connection and fetch parameters accordingly
def fetch_wireless_parameters():
    if user_prompt('Are you connecting the raspberry pi to a wireless internet connection'):
        while True:
            sys.stdout.write('Enter the Wireless network SSID : ')
            wifi_ssid = input()
            if len(wifi_ssid):
                break
            else:
                print('[ERROR] Please enter an Wireless network SSID')
    else:
        print('Note: The wired internet connection MUST be through the ethernet adapter connected to the USB port')
        return None, None, None

    wifi_username = None

    # WPA-EAP requires an username and password for connecting to the network. Typical enterprise config
    # WPA-PSK requires only a password (pre-shared key) for connecting to network. Typical home network
    if user_prompt('Are you trying to connect to an WPA-Enterprise which requires an username for connection'):
        while True:
            sys.stdout.write('Enter the Username required for connecting to the Wireless network : ')
            wifi_username = input()
            if len(wifi_username):
                break
            else:
                print('[ERROR] Please enter an Username for authenticating with the Wireless network')

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
    try:
        settings.backup_file(config_file)
    except OSError as error:
        if 'Permission denied' in error.strerror:
            print("[ERROR] Code is executed as a non privileged user."
                  "\n[ERROR] Please re-run the script as superuser. [ sudo ./{} ]".format(os.path.basename(__file__)))
            sys.exit()
        print('[ERROR] Unknown error occurred while accessing {} file'.format(config_file))
        print('[ERROR] {}'.format(error.strerror))
        sys.exit()

    with open(config_file, 'a') as file_object:
        file_object.write('gpu_mem=16')

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
    with open('/boot/ssh', 'w') as file_object:
        file_object.write('')

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
def dns_configuration(base_path, wireless):
    print('Setting up the dynamic dns configuration')
    file_name = '/dynv6.sh'
    path_name = '/etc/dns'
    token_file_name = '/dynv6_token.txt'

    if wireless is None:
        device = 'eth1'
    else:
        device = 'wlan0'

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

    with open(base_path + token_file_name, 'r') as file_object:
        data = file_object.readlines()

    dns_token = None

    for string in data:
        if len(string) > 0:
            if string.strip()[0] != '#' and 'token' in string.strip():
                dns_token = string.strip().split('=')[1].strip()

    if dns_token is None or dns_token is 'TOKEN_WILL_REPLACE_THIS':
        print(('[ERROR] The file {} does not have a valid dynv6_token.\n'
               'Check out https://dynv6.com/docs/apis for token.\n'
               'Then token must be present in the file of the form "token = YOUR TOKEN"\n'
               ).format(file_name))
        sys.exit()

    subprocess.check_output(['sed', '-i', '--',
                             's|token="YOUR_DYNV6_TOKEN_HERE"|token="' + dns_token + '"|g',
                             path_name + file_name])

    subprocess.check_output(['sed', '-i', '--',
                             's|hostname="YOUR_DOMAIN_NAME_HERE"|hostname="' + settings.DOMAIN_NAME + '"|g',
                             path_name + file_name])

    subprocess.check_output(['sed', '-i', '--',
                             's|device="YOUR_NETWORK_DEVICE_NAME_HERE"|device="' + device + '"|g',
                             path_name + file_name])


# Create Wifi configuration for connecting to Wireless network or not if wired.
# Creates the interface configuration for the scientific instrument.
def network_configuration(wifi_ssid, wpa_username, wpa_password, no_dynamic_dns, manual_config):
    print('Setting up the internet configuration')

    # For wifi configuration
    wpa_config_file = '/etc/wpa_supplicant/wpa_supplicant.conf'
    interfaces_file = '/etc/network/interfaces'

    loopback_config = (
        '\nauto lo\n'
        'iface lo inet loopback\n'
    )

    ethernet_config_instrument = (
        '\nauto eth0\n'
        'iface eth0 inet static\n'
        '\taddress 192.168.7.1\n'
        '\tnetmask 255.255.255.0\n'
        '\tnetwork 192.168.7.0\n\n'
    )

    # Taking a backup of interfaces file
    settings.backup_file(interfaces_file)

    ethernet_config_internet = (
        '\nauto eth1\n'
        'iface eth1 inet dhcp\n'
        'iface eth1 inet6 dhcp\n'
    )

    # Wired internet connection
    if wifi_ssid is None:

        write_values = loopback_config + ethernet_config_instrument

        if not manual_config:
            write_values = write_values + ethernet_config_internet

        with open(interfaces_file, 'a') as file_object:
            file_object.write(write_values)
        return

    # Wireless internet connection
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

    wifi_config_list = [
        '\nauto wlan0\n',
        'allow-hotplug wlan0\n',
        'iface wlan0 inet dhcp\n',
        '\twpa-conf /etc/wpa_supplicant/wpa_supplicant.conf\n'
        # '\tpre-up /bin/bash /etc/firewall/iptables.sh\n'
    ]

    if not no_dynamic_dns:
        wifi_config_list.append('\tpost-up /bin/bash /etc/dns/dynv6.sh\n')

    print('Adding WPA configuration to {} file'.format(wpa_config_file))
    settings.backup_file(wpa_config_file)
    with open(wpa_config_file, 'a') as file_object:
        file_object.write(final_wpa_config)

    print('Adding WIFI configuration to {} file'.format(interfaces_file))
    with open(interfaces_file, 'a') as file_object:
        file_object.write(loopback_config + ethernet_config_instrument + ''.join(wifi_config_list))


# Rebooting the raspberry pi
def clean_up_setup():
    print('Rebooting the system in 5 seconds...')
    time.sleep(5)
    subprocess.check_output(['reboot', 'now'])


if __name__ == '__main__':
    arguments = fetch_argument()
    no_dns = arguments.nodns
    manual = arguments.manual
    settings.test_values()
    base_directory = file_directory()
    ssid, username, password = fetch_wireless_parameters()
    pi_configuration()
    firewall_configuration(base_directory)
    if not no_dns:
        dns_configuration(base_directory, ssid)
    network_configuration(ssid, username, password, no_dns, manual)
    clean_up_setup()
