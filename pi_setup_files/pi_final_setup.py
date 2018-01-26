#!/usr/bin/env python3

import argparse
import os
import shutil
import socket
import subprocess
import sys
import time

import pi_settings as settings


# Fetches arguments from the user
def fetch_arguments():
    parser = argparse.ArgumentParser(description='Raspberry Pi setup part-2')

    parser.add_argument('-t', '--testing',
                        help='Testing mode. Obtains invalid server certificate from letsencrypt',
                        action='store_true'
                        )

    parser.add_argument('-e', '--email',
                        help='This email address will be used to recover server certificate key using letsencrypt',
                        required=True
                        )

    args = parser.parse_args()
    return args


# This method Upgrades all existing packages
# Note: upgrade only after installing and configuring all other packages
# In the case of kernel upgrades, it requires restart and trying to
# configure packages before restart causes exceptions.
def upgrade_packages():
    print('Upgrading existing packages')
    subprocess.call(['apt-get', '-y', 'upgrade'])


# Installs all required packages for our application
def install_packages():
    packages = ['isc-dhcp-server', 'nmap', 'git', 'apache2', 'python3-requests', 'python-certbot-apache']

    # Prefer IPV4 over IPV6 for downloading updates
    # subprocess.check_output(['sed', '-i', '--',
    #                         's|#precedence ::ffff:0:0/96  100|precedence ::ffff:0:0/96  100|g',
    #                         '/etc/gai.conf'])

    print('Updating packages existing packages')
    subprocess.call(['apt-get', 'update'])
    print('Installing the following packages {}'.format(", ".join(packages)))
    subprocess.call(['sudo', 'DEBIAN_FRONTEND=noninteractive', 'apt-get', '-y', 'install'] + packages)

    #Installing certbot separately from source
    subprocess.call(['wget', '-P', '/home/pi/','https://dl.eff.org/certbot-auto'])
    subprocess.call(['sudo', 'chmod', 'a+x', '/home/pi/certbot-auto'])



    # Resetting the preferences to default
    # subprocess.check_output(['sed', '-i', '--',
    #                         's|precedence ::ffff:0:0/96  100|#precedence ::ffff:0:0/96  100|g',
    #                         '/etc/gai.conf'])


def isc_dhcp_server_configuration():
    dhcpd_file = '/etc/dhcp/dhcpd.conf'
    dhcpd_backup = '/etc/dhcp/dhcpd_backup.conf'

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

    print('Adding the raspberry pi dhcp server configuration to {} file'.format(dhcpd_file))
    if not os.path.isfile(dhcpd_backup):
        shutil.copy2(dhcpd_file, dhcpd_backup)
    else:
        shutil.copy2(dhcpd_backup, dhcpd_file)
    with open(dhcpd_file, 'w') as file:
        file.write(dhcp_config)

    subprocess.check_output(['sed', '-i', '--',
                             's|INTERFACESv4=""|INTERFACESv4="eth0"|g',
                             '/etc/default/isc-dhcp-server'])
    print('Restarting the dhcp server service')
    subprocess.check_output(['service', 'isc-dhcp-server', 'restart'])


# Sets up https configuration for apache
def tls_configuration(email_address, test):
    ssl_config_file = '/etc/apache2/sites-available/000-default-le-ssl.conf'

    if os.path.isdir('/etc/letsencrypt/live/' + settings.DOMAIN_NAME) and os.path.isfile(ssl_config_file):
        print('HTTPS already configured')
        return

    # Update DNS Record before getting certificate
    subprocess.check_output('/etc/dns/dynv6.sh')

    certbot_arguments = ['sudo', '/home/pi/certbot-auto', '-n', '--apache', '-d', settings.DOMAIN_NAME]

    if test:
        certbot_arguments.append('--staging')

    certbot_arguments.extend(['--redirect', '--agree-tos', '--email', email_address])

    print('Setting up HTTPS support for the website')
    subprocess.check_output(certbot_arguments)


# Creating configuration to proxy requests to the tomcat container
def apache_configuration():
    print("Creating the Reverse Proxy Configuration and securing Apache server")

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
        '\n# Hiding apache web server signature'
        '\nServerSignature Off'
        '\nServerTokens Prod\n'
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

    ssl_config_file = '/etc/apache2/sites-available/000-default-le-ssl.conf'
    ssl_config_backup = '/etc/apache2/sites-available/000-default-le-ssl_backup.conf'

    with open(ssl_config_file, 'r') as file:
        contents = file.readlines()

    if len(contents) == 0:
        print('[ERROR]The {} file has no contents'.format(ssl_config_file))
        sys.exit()

    if not os.path.isfile(ssl_config_backup):
        shutil.copy2(ssl_config_file, ssl_config_backup)
    else:
        shutil.copy2(ssl_config_backup, ssl_config_file)

    with open(ssl_config_file, 'w') as file:
        for line in contents:
            file.write(line)
            if line.strip() == 'DocumentRoot /var/www/html':
                file.write(hsts_config + proxy_config + ocsp_stapling_config + miscellaneous_headers)

    ssl_mod_file = '/etc/apache2/mods-available/ssl.conf'
    ssl_mod_backup = '/etc/apache2/mods-available/ssl_backup.conf'

    with open(ssl_mod_file, 'r') as file:
        contents = file.readlines()

    if len(contents) == 0:
        print('[ERROR]The {} file has no contents'.format(ssl_mod_file))
        sys.exit()

    if not os.path.isfile(ssl_mod_backup):
        shutil.copy2(ssl_mod_file, ssl_mod_backup)
    else:
        shutil.copy2(ssl_mod_backup, ssl_mod_file)

    with open(ssl_mod_file, 'w') as file:
        for line in contents:
            file.write(line)
            if line.strip() == '<IfModule mod_ssl.c>':
                file.write(ssl_stapling_cache)

    apache_config_file = '/etc/apache2/apache2.conf'
    apache_config_backup = '/etc/apache2/apache2_backup.conf'

    if not os.path.isfile(apache_config_backup):
        shutil.copy2(apache_config_file, apache_config_backup)
    else:
        shutil.copy2(apache_config_backup, apache_config_file)

    with open(apache_config_file, 'a') as file:
        file.write(apache_signature_config)

    # Disabling directory browsing
    subprocess.check_output(['sed', '-i', '--',
                             's|Options Indexes FollowSymLinks|Options FollowSymLinks|g',
                             apache_config_file])

    # Remove index file from /var/www/html
    try:
        os.remove('/var/www/html/index.html')
    except OSError as error:
        if 'No such file or directory' not in error.strerror:
            print('[WARNING] Unable to delete index.html file from document root (/var/www/html) of apache.')
            print('[DEBUG] Error was {}'.format(error))


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

    if os.path.isdir(path):
        print('Guacamole setup files already exists in {}'.format(path))
        return

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
    upgrade_packages()
    print('Rebooting the system in 5 seconds...')
    time.sleep(5)
    subprocess.check_output(['reboot', 'now'])


# Checks internet connectivity by trying tcp connect to archive.raspberrypi.org
# Fails in case archive.raspberrypi.org is down (highly unlikely) or if dns resolver fails
def check_internet_connectivity():
    print('Testing Internet Connectivity')
    connected = False
    try:
        host = 'archive.raspberrypi.org'
        socket.create_connection((host, 80))
        connected = True
    except OSError:
        pass

    if not connected:
        print('[ERROR] No internet connectivity. Please check if pi connected to wifi network'
              'If not verify the wpa_supplicant config file'
              'If connected to Wireless network, check if archive.raspberrypi.org is down (Unlikely!)')
        sys.exit()

    print('The pi is has internet connectivity.')


if __name__ == '__main__':
    arguments = fetch_arguments()
    settings.test_values()
    check_internet_connectivity()
    email = arguments.email
    testing = arguments.testing
    install_packages()
    isc_dhcp_server_configuration()
    docker_install()
    guacamole_configuration()
    tls_configuration(email, testing)
    apache_configuration()
    setup_cronjobs()
    clean_up_setup()
