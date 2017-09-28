#!/usr/bin/env python3

import argparse
import getpass
import os
import shutil
import subprocess
import time

DOMAIN_NAME = 'mini-dmz.dynv6.net'


def file_directory():
    path = os.path.dirname(os.path.realpath(__file__))
    return path


# Obtain command line arguments
def fetch_argument():
    parser = argparse.ArgumentParser(description='Sets up the Raspberry Pi')
    parser.add_argument('-u', '--username',
                        help='IU Username to connect to the IU Wireless network',
                        required=True
                        )
    iu_username = parser.parse_args().username

    while True:

        iu_password = getpass.getpass('Enter IU Password : ')
        iu_verify_password =  getpass.getpass('Re-enter IU Password : ')

        if iu_password == iu_verify_password:
            break
        else:
            print("[Error] The passwords do not match. Please enter again.")

    return iu_username, iu_password


# Configurations directly modifying pi
def pi_configuration():

    # Forcing user to change default pi password
    print('Please change the default Rapberry Pi password')
    subprocess.check_output('passwd pi', shell=True)

    # Pi for a headless application then you can reduce the memory split
    # between the GPU and the rest of the system down to 16mb
    print('Setting GPU memory to 16mb')
    with open('/boot/config.txt', 'a') as file:
        file.write('gpu_mem=16')

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

    firewall_path = '/etc/firewall'
    firewall_script_name = '/iptables.sh'

    # Creating the folder for our firewall script file
    os.makedirs(firewall_path)

    # copying iptables rules to the new folder
    shutil.copy2(base_path + firewall_script_name, firewall_path + firewall_script_name)

    # Changing file permissions
    os.chmod(firewall_path + firewall_script_name, 0o770)
    subprocess.check_output(['chown', 'pi', firewall_path + firewall_script_name])


# Create the firewall configuration for the raspberry pi
def dns_configuration(base_path):
    file_name = '/dynv6.sh'
    path_name = '/etc/dns'
    # Creating the folder for our dns script file
    os.makedirs('/etc/dns')
    # copying dns script to the new folder
    shutil.copy2(base_path + file_name, path_name + file_name)

    # Changing file permissions
    os.chmod(path_name + file_name, 0o770)
    subprocess.check_output(['chown', 'pi', path_name + file_name])

    with open('dynv6_token.txt', 'r') as file:
        data = file.readlines()

    dns_token = None

    for string in data:
        if string.strip()[0] != '#' and 'token' in string.strip():
            dns_token = string.strip().split('=')[1].strip()

    if dns_token is None:
        print(('[ERROR] The file {} does not have a valid dynv6_token.\n' 
               'Check out https://dynv6.com/docs/apis for token.\n'
               'Then token must be present in the file of the form "token = YOUR TOKEN"\n'
               ).format(file_name))
        sys.exit()

    subprocess.check_output(['sed', '-i', '--',
                             's|token="YOUR_DYNV6_TOKEN_HERE"|token="'+ dns_token + '"|g',
                             path_name + file_name])

    subprocess.check_output(['sed', '-i', '--',
                             's|hostname="YOUR_DOMAIN_NAME_HERE"|hostname="' + DOMAIN_NAME + '"|g',
                             path_name + file_name])


# Create Wifi configuration for connecting to IU Secure network
# Adds script to initialize firewall rules
# Adds script to register ip with dynv6 service
# Todo: token for dynamic dns remove hardcoded value
def wifi_configuration(username, password):

    wpa_config = (
        '\tssid="IU Secure"\n'
        '\tkey_mgmt=WPA-EAP\n'
        '\tpairwise=CCMP TKIP\n'
        '\tgroup=CCMP TKIP\n'
        '\teap=PEAP\n'
        '\tphase1="peapver=0"\n'
        '\tphase2="MSCHAPV2"\n'
        '\tidentity="{}"\n'
        '\tpassword="{}"\n'
    ).format(username, password)

    final_wpa_config = '\nnetwork={\n' + wpa_config + '}\n'

    interface_config = (
        '\nauto wlan0\n'
        'allow-hotplug wlan0\n'
        'iface wlan0 inet dhcp\n'
        '\tpre-up wpa_supplicant -B -Dwext -i wlan0 -c/etc/wpa_supplicant/wpa_supplicant.conf\n'
        '\tpre-up /bin/bash /etc/firewall/iptables.sh\n'
        '\tpost-up /bin/bash /etc/dns/dynv6.sh\n'
        '\tpost-down killall -q wpa_supplicant\n'
    )
    print('Adding WPA configuration to /etc/wpa_supplicant/wpa_supplicant.conf.conf file')
    with open('/etc/wpa_supplicant/wpa_supplicant.conf', 'a') as file:
        file.write(final_wpa_config)

    print('Adding WIFI configuration to /etc/network/interfaces file')
    with open('/etc/network/interfaces', 'a') as file:
        file.write(interface_config)


# The raspberry pi acts as a router for the scientific device at
# the ethernet interface
def ethernet_configuration():
    ethernet_config = (
        '\nauto eth0\n'
        'iface eth0 inet static\n'
        'address 192.168.0.1\n'
        'netmask 255.255.255.0\n'
    )
    print('Adding the scientific device connection configuration to /etc/network/interfaces file')
    with open('/etc/network/interfaces', 'a') as file:
        file.write(ethernet_config)


# Rebooting the raspberry pi
def clean_up_setup():
    print('Rebooting the system in 5 seconds...')
    time.sleep(5)
    subprocess.check_output(['reboot', 'now'])


if __name__ == '__main__':
    username, password = fetch_argument()
    base_directory = file_directory()
    pi_configuration()
    firewall_configuration(base_directory)
    wifi_configuration(username, password)
    dns_configuration(base_directory)
    ethernet_configuration()
    clean_up_setup()
