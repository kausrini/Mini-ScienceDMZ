#!/usr/bin/env python2.7

import argparse
import getpass
import os
import shutil
import subprocess
import time


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

    # Prefer IPV4 over IPV6 for downloading updates
    subprocess.check_output(['sed', '-i', '--',
                             's|#precedence ::ffff:0:0/96  100|precedence ::ffff:0:0/96  100|g',
                             '/etc/gai.conf'])


# Create the firewall configuration for the raspberry pi
def firewall_configuration():

    # Creating the folder for our firewall script file
    os.makedirs('/etc/firewall')

    # copying iptables rules to the new folder
    shutil.copy2('iptables.rules', '/etc/firewall/iptables.sh')

    # Changing file permissions
    os.chmod('/etc/firewall/iptables.sh', 0o700)


# Create Wifi configuration for connecting to IU Secure network
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
        '\nallow-hotplug wlan0\n'
        'iface wlan0 inet dhcp\n'
        '\tpre-up wpa_supplicant -B -Dwext -i wlan0 -c/etc/wpa_supplicant/wpa_supplicant.conf\n'
        '\tpre-up /bin/bash /etc/firewall/iptables.sh\n'
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
    pi_configuration()
    firewall_configuration()
    wifi_configuration(username, password)
    ethernet_configuration()
    clean_up_setup()
