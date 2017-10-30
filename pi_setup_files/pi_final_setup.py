#!/usr/bin/env python3

import argparse
import subprocess
import getpass
import time
import os
import sys

DOMAIN_NAME = 'mini-dmz-developer.dynv6.net'
# The following email address can be used to recover Server Certificate key
EMAIL_ADDRESS = 'kausrini@iu.edu'


# Installs all required packages for our application
def install_packages():
    packages = ['isc-dhcp-server', 'nmap','git', 'apache2', 'python-certbot-apache', 'python3-requests']

    # Prefer IPV4 over IPV6 for downloading updates
    subprocess.check_output(['sed', '-i', '--',
                             's|#precedence ::ffff:0:0/96  100|precedence ::ffff:0:0/96  100|g',
                             '/etc/gai.conf'])

    print('Upgrading existing packages')
    subprocess.call(['apt-get', 'update'])
    subprocess.call(['apt-get', '-y', 'upgrade'])
    print('Installing the following packages {}'.format(", ".join(packages)))
    subprocess.call(['sudo', 'DEBIAN_FRONTEND=noninteractive', 'apt-get', '-y', 'install'] + packages)

    # Resetting the preferences to default
    subprocess.check_output(['sed', '-i', '--',
                             's|precedence ::ffff:0:0/96  100|#precedence ::ffff:0:0/96  100|g',
                             '/etc/gai.conf'])


def isc_dhcp_server_configuration():
    dhcp_config = (
        '\nddns-update-style none;\ndeny declines;\ndeny bootp;\n'
        'subnet 192.168.7.0 netmask 255.255.255.0 {\n'
        '\trange 192.168.7.2 192.168.7.254;\n'
        '\toption routers 192.168.7.1;\n'
        '\toption broadcast-address 192.168.7.255;\n'
        '\tdefault-lease-time 3600;\n'
        '\tmax-lease-time 7200;\n'
        '}'
    )

    print('Adding the raspberry pi dhcp server configuration to /etc/dhcp/dhcpd.conf file')
    with open('/etc/dhcp/dhcpd.conf', 'w') as file:
        file.write(dhcp_config)

    subprocess.check_output(['sed', '-i', '--',
                            's|INTERFACESv4=""|INTERFACESv4="eth0"|g',
                            '/etc/default/isc-dhcp-server'])
    print('Restarting the dhcp server service')
    subprocess.check_output(['service', 'isc-dhcp-server', 'restart'])


# Creating configuration to proxy requests to the tomcat container
def reverse_proxy_configuration():
    print("Creating the Reverse Proxy Configuration")

    # The first proxy pass MUST be to websocket tunnel.
    # If the first proxy pass is for just guacamole connection defaults to HTTP Tunnel
    # and causes degraded performance, file transfer breaks.
    # Note that proxy is to localhost port 8080. Hence container port 8080 should be binded to localhost:8080
    proxy_config = (
        '\n\tProxyPass /guacamole/websocket-tunnel ws://127.0.0.1:8080/guacamole/websocket-tunnel \n'
        '\tProxyPassReverse /guacamole/websocket-tunnel ws://127.0.0.1:8080/guacamole/websocket-tunnel \n\n'
        '\tProxyPass /guacamole/ http://127.0.0.1:8080/guacamole/ flushpackets=on \n'
        '\tProxyPassReverse /guacamole/ http://127.0.0.1:8080/guacamole/ \n\n'
    )

    subprocess.check_output(['a2enmod', 'proxy_http'])
    subprocess.check_output(['a2enmod', 'proxy_wstunnel'])

    with open('/etc/apache2/sites-enabled/000-default-le-ssl.conf', 'r') as file:
        contents = file.readlines()

    if len(contents) == 0:
        print('[ERROR]The /etc/apache2/sites-enabled/000-default-le-ssl.conf file has no contents')
        sys.exit()

    with open('/etc/apache2/sites-enabled/000-default-le-ssl.conf', 'w') as file:
        for line in contents:
            file.write(line)
            if line.strip() == 'DocumentRoot /var/www/html':
                file.write(proxy_config)


def ssl_configuration():

    # Update DNS Record before getting certificate
    subprocess.check_output('/etc/dns/dynv6.sh')

    print('Setting up HTTPS support for our website')
    subprocess.check_output(['certbot', '-n', '--apache',
                             '-d', DOMAIN_NAME,
                             '--redirect', '--staging', '--agree-tos',
                             '--email', EMAIL_ADDRESS])


# Installing docker
def docker_install():
    print('Installing Docker module')
    subprocess.call('curl -sSL https://get.docker.com | sh', shell=True)
    subprocess.check_output(['systemctl', 'enable', 'docker'])
    subprocess.check_output(['systemctl', 'start', 'docker'])
    subprocess.check_output(['usermod', '-aG', 'docker', 'pi'])


# Downloading our application from our git repository
def guacamole_configuration():
    path = '/home/pi/minidmz'
    git_command = 'git clone https://github.com/kausrini/Mini-ScienceDMZ.git {}'.format(path)
    print('Fetching the guacamole setup files from git repository')
    subprocess.check_output(['runuser', '-l', 'pi', '-c', git_command])
    subprocess.check_output(['chmod', '774', path + '/guacamole_setup_files/setup.py'])


def setup_cronjobs():

    # Update dns after reboot.
    # Update dns every one hour.
    # Start docker containers on boot (Todo Python script for this with proper checks of existence of containers)
    cron_jobs = (
        '@reboot /etc/dns/dynv6.sh\n'
        '0 * * * * /etc/dns/dynv6.sh\n'
        '@reboot docker start sql_container\n'
        '@reboot docker start guacamole_container\n'
    )

    cron_file_name = 'temp_cron'
    file_path = '/tmp/' + cron_file_name

    with open(file_path, 'w') as file:
        file.write(cron_jobs)

    subprocess.check_output(['crontab', file_path])
    os.remove(file_path)


# Rebooting the raspberry pi
def clean_up_setup():
    print('Rebooting the system in 5 seconds...')
    time.sleep(5)
    subprocess.check_output(['reboot', 'now'])


if __name__ == '__main__':
    install_packages()
    isc_dhcp_server_configuration()
    docker_install()
    guacamole_configuration()
    ssl_configuration()
    reverse_proxy_configuration()
    setup_cronjobs()
    clean_up_setup()
