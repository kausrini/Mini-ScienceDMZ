#!/usr/bin/env python3

import argparse
import subprocess
import getpass
import time
import os
import sys

DOMAIN_NAME = 'mini-science-dmz.dynv6.net'
# The following email address can be used to recover Server Certificate key
EMAIL_ADDRESS = 'kausrini@iu.edu'

# Installs all required packages for our application
def install_packages():
    packages = ['dnsmasq', 'git', 'apache2', 'python-certbot-apache', 'python3-requests']

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


# The raspberry pi acts as a router for the scientific device at
# the ethernet interface
def dhcp_server_configuration():
    dhcp_config = (
        '\ninterface=eth0\n'
        'dhcp-range=192.168.0.7,192.168.0.7,255.255.255.0,infinite\n'
    )

    print('Adding the raspberry pi dhcp server configuration to /etc/dnsmasq.conf file')
    with open('/etc/dnsmasq.conf', 'a') as file:
        file.write(dhcp_config)

    print('Restarting the dhcp server service')
    subprocess.check_output(['service', 'dnsmasq', 'restart'])

# Creating configuration to proxy requests to the tomcat container
def apache_configuration():
    print("Creating the Reverse Proxy Configuration")

    # The first proxy pass MUST be to websocket tunnel.
    # If the first proxy pass is for just guacamole connection defaults to HTTP Tunnel
    # and causes degraded performance, file transfer breaks.
    # Note that proxy is to localhost port 8080. Hence container port 8080 should be binded to localhost:8080
    proxy_config = (
        '\n\n\t# Proxy configuration'
        '\n\tProxyPass /guacamole/websocket-tunnel ws://127.0.0.1:8080/guacamole/websocket-tunnel'
        '\n\tProxyPassReverse /guacamole/websocket-tunnel ws://127.0.0.1:8080/guacamole/websocket-tunnel'
        '\n\n\tProxyPass /guacamole/ http://127.0.0.1:8080/guacamole/ flushpackets=on'
        '\n\tProxyPassReverse /guacamole/ http://127.0.0.1:8080/guacamole/'
    )

    # OSCP stapling configuration for our server
    ocsp_stapling_config = (
        '\n\n\t#OSCP Stapling Configuration'
        '\n\tSSLUseStapling on'
        '\n\tSSLStaplingReturnResponderErrors off'
        '\n\tSSLStaplingResponderTimeout 5'
        '\n\n'
    )
    ssl_stapling_cache = (
        '\n\n\t# The SSL Stapling Cache global parameter'
        '\n\tSSLStaplingCache shmcb:${APACHE_RUN_DIR}/ssl_stapling_cache(128000)'
        '\n'
    )

    # HSTS configuration
    hsts_config = (
        '\n\n\t# HSTS for 1 year including the subdomains'
        '\n\tHeader always set Strict-Transport-Security "max-age=31536000; includeSubDomains"'
        '\n'
    )

    # Hiding apache web server signature
    apache_signature_config = (
        '\n\n\t# Hiding apache web server signature'
        '\nServerSignature Off'
        '\nServerTokens Prod'
        '\n'
    )

    # Other headers
    miscellaneous_headers = (
        '\n\tHeader set X-Content-Type-Options nosniff'
        '\n\tHeader always set X-Frame-Options "SAMEORIGIN"'
        '\n\tHeader always set X-Xss-Protection "1; mode=block"'
    )


    # For proxying
    subprocess.check_output(['a2enmod', 'proxy_http'])
    subprocess.check_output(['a2enmod', 'proxy_wstunnel'])

    # For enabling HSTS
    subprocess.check_output(['a2enmod', 'headers'])

    with open('/etc/apache2/sites-enabled/000-default-le-ssl.conf', 'r') as file:
        contents = file.readlines()

    if len(contents) == 0:
        print('[ERROR]The /etc/apache2/sites-enabled/000-default-le-ssl.conf file has no contents')
        sys.exit()

    with open('/etc/apache2/sites-enabled/000-default-le-ssl.conf', 'w') as file:
        for line in contents:
            file.write(line)
            if line.strip() == 'DocumentRoot /var/www/html':
                file.write(hsts_config + proxy_config + ocsp_stapling_config + miscellaneous_headers)

    with open('/etc/apache2/mods-enabled/ssl.conf', 'r') as file:
        contents = file.readlines()

    if len(contents) == 0:
        print('[ERROR]The /etc/apache2/mods-enabled/ssl.conf file has no contents')
        sys.exit()

    with open('/etc/apache2/mods-enabled/ssl.conf', 'w') as file:
        for line in contents:
            file.write(line)
            if line.strip() == '<IfModule mod_ssl.c>':
                file.write(ssl_stapling_cache)

    with open('/etc/apache2/mods-enabled/ssl.conf', 'a') as file:
        file.write(apache_signature_config)


def ssl_configuration():
    # Update DNS Record before getting certificate
    subprocess.check_output('/etc/dns/dynv6.sh')

    print('Setting up HTTPS support for our website')
    subprocess.check_output(['certbot', '-n', '--apache',
                             '-d', DOMAIN_NAME,
                             '--redirect', '--agree-tos',
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
    dhcp_server_configuration()
    docker_install()
    guacamole_configuration()
    ssl_configuration()
    apache_configuration()
    setup_cronjobs()
    clean_up_setup()
