#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import sys
import time

from pathlib import Path

import pi_settings as settings
import perfsonar_install as perfinst


# Fetches arguments from the user
def fetch_arguments():
    parser = argparse.ArgumentParser(description='Raspberry Pi setup part-2')

    parser.add_argument('-t', '--testing',
                        help='Testing mode. Obtains invalid server certificate from letsencrypt',
                        action='store_true'
                        )

    parser.add_argument('-e', '--email',
                        help='This email address will be used to recover server certificate key using letsencrypt',
                        )

    parser.add_argument('-i', '--insecure',
                        help='Sets up insecure/HTTP configuration for apache reverse proxy',
                        action='store_true'
                        )

    parser.add_argument('-s', '--self',
                        help='Sets up self-signed configuration for apache reverse proxy',
                        action='store_true'
                        )

    parser.add_argument('-a', '--saml',
                        help='Sets up SAML authentication',
                        action='store_true'
                        )

    parser.add_argument('-p', '--perfsonar',
                        help='Sets up Perfsonar',
                        action='store_true'
                        )

    args = parser.parse_args()
    return args


# This method Upgrades all existing packages
# Note: upgrade only after installing and configuring all other packages
# In the case of kernel upgrades, it requires restart and trying to
# configure packages before restart causes exceptions.
def upgrade_packages():
    print('Upgrading existing packages')
    subprocess.check_call(['apt-get', '-y', 'upgrade'])


def update_packages():
    print('Updating apt')
    subprocess.check_call(['apt-get', 'update'])


# Installs all required packages for our application
def install_packages(http_setup):

    apt_sources_file = '/etc/apt/sources.list'

    # Adding stretch backports
    with open(apt_sources_file, 'a') as file_object:
        file_object.write('\ndeb http://ftp.debian.org/debian stretch-backports main')


    update_packages()

    packages = ['isc-dhcp-server', 'nmap', 'git', 'apache2', 'python3-requests',
                'iptables-persistent']

    print('Installing the following packages {}'.format(", ".join(packages)))
    try:
        subprocess.check_call(['sudo', 'DEBIAN_FRONTEND=noninteractive', 'apt-get', '-y', 'install'] + packages)
    except subprocess.CalledProcessError as error:
        print("[ERROR] One of the packages is not correctly installed, please check the installation.")
        print(error)
        sys.exit()


# Sets up the dhcp server configuration
def isc_dhcp_server_configuration():
    dhcpd_file = '/etc/dhcp/dhcpd.conf'

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

    settings.backup_file(dhcpd_file)
    with open(dhcpd_file, 'w') as file_object:
        file_object.write(dhcp_config)

    subprocess.check_output(['sed', '-i', '--',
                             's|INTERFACESv4=""|INTERFACESv4="eth0"|g',
                             '/etc/default/isc-dhcp-server'])
    print('Restarting the dhcp server service')
    subprocess.check_output(['service', 'isc-dhcp-server', 'restart'])


# Sets up https configuration for apache
# Returns false if certbot setup was successful
def certbot_tls_configuration(email_address, test):
    certbot_setup = False
    ssl_config_file = '/etc/apache2/sites-available/000-default-le-ssl.conf'
    update_packages()
    # Install certbot package
    try:
        subprocess.check_call(['DEBIAN_FRONTEND=noninteractive', 'apt-get', '-y', 'install', 'python-certbot-apache', '-t', 'stretch-backports'])
    except subprocess.CalledProcessError as error:
        print("[ERROR] One of the packages is not correctly installed, please check the installation.")
        print(error)
        sys.exit()

    if os.path.isdir('/etc/letsencrypt/live/' + settings.DOMAIN_NAME) and os.path.isfile(ssl_config_file):
        print('HTTPS already configured')
        return

    # Update DNS Record before getting certificate
    try:
        subprocess.check_output('/etc/dns/dynv6.sh')
    except OSError:
        if 'No such file or directory':
            print('[Warning] No dynamic dns script detected.')

    certbot_arguments = ['sudo', '/home/pi/certbot-auto', '-n', '--apache', '-d', settings.DOMAIN_NAME]

    if test:
        certbot_arguments.append('--staging')

    certbot_arguments.extend(['--redirect', '--agree-tos', '--email', email_address])

    print('Setting up HTTPS support for the website')
    try:
        subprocess.check_output(certbot_arguments)
    except subprocess.CalledProcessError as error:
        print('[ERROR] Certbot setup failed due to following error. This setup shall proceed with configuring '
              'self-signed apache reverse proxy as an alternative')
        print(error)
        certbot_setup = True

    return certbot_setup


# Writes proxy configuration to http virtual host if http setup
# Else writes redirection code to http virtual host if https setup
def apache_http_configuration(proxy_config, auth_config, miscellaneous_headers, https_redirection):
    default_cofig_path = '/etc/apache2/sites-available/'
    default_config_name = '000-default.conf'
    default_config_file = default_cofig_path + default_config_name

    if https_redirection:
        write_contents = '\n\tRewriteEngine on\n\tRewriteCond %{SERVER_NAME} =' + settings.DOMAIN_NAME + \
                         '\n\tRewriteRule ^ https://%{SERVER_NAME}%{REQUEST_URI} ' \
                         '[END,NE,R=permanent]\n'
    else:
        write_contents = proxy_config + auth_config + miscellaneous_headers

    settings.backup_file(default_config_file)

    with open(default_config_file, 'r') as file:
        default_contents = file.readlines()

    if len(default_contents) == 0:
        print('[ERROR]The {} file has no contents'.format(default_config_file))
        sys.exit()

    with open(default_config_file, 'w') as file:
        for line in default_contents:
            file.write(line)
            if line.strip() == 'DocumentRoot /var/www/html':
                file.write(write_contents)

    # Enabling the http virtual host
    subprocess.check_output(['a2ensite', default_config_name])


# https configuration common to certbot and self-signed setup
def https_config(ssl_configuration, auth_config, ssl_config_file):
    settings.backup_file(ssl_config_file)

    with open(ssl_config_file, 'r') as file:
        contents = file.readlines()

    if len(contents) == 0:
        print('[ERROR]The {} file has no contents'.format(ssl_config_file))
        sys.exit()

    with open(ssl_config_file, 'w') as file:
        for line in contents:
            file.write(line)
            if line.strip() == 'DocumentRoot /var/www/html':
                file.write(ssl_configuration + auth_config)


# self signed https configuration.
def apache_self_signed_configuration(ssl_config_file, email_address, domain_name):
    cert_path = '/etc/minidmz_certs/'
    # dh_param_file = 'dhparam.pem'

    # Enabling rewrite engine for apache2 https redirection
    subprocess.check_output(['a2enmod', 'rewrite'])

    # Create folder for certificate and private keys
    try:
        print('Creating certificate path at {}'.format(cert_path))
        os.makedirs(cert_path)
    except OSError as error:
        if 'File exists' in error.strerror:
            print('Certificate folder exists at {}'.format(cert_path))
            pass
        else:
            print(error)
            sys.exit()

    cert_generation_command = ('openssl req -x509 -nodes -days 365 -newkey rsa:4096 -keyout {}.key -out {}.crt -subj'
                               ' "/C=US/ST=Indiana/L=Bloomington/O=Indiana University/OU=UITS/'
                               'CN={}/emailAddress={}"').format(cert_path + domain_name, cert_path + domain_name,
                                                                domain_name, email_address)

    # TODO: Make DH group generation optional. Ask user if they want more secure tls connections.
    # Warn them it'll take additional 30 mins of setup time.
    # diffie_hellman_group_command = ['openssl', 'dhparam', '-out', cert_path + dh_param_file, '2048']
    # print('Generating Diffie-Hellman Group for negotiating perfect forward secrecy.This will take around 30 minutes!')
    # subprocess.check_output(diffie_hellman_group_command)

    # Generate certificate and key
    print('Generating a Self-Signed Certificate')
    subprocess.check_output(cert_generation_command, shell=True)

    # Write to ssl virtual host file for apache
    contents = '<IfModule mod_ssl.c>\n<VirtualHost *:443>\n\tServerAdmin webmaster@localhost' \
               '\n\tDocumentRoot /var/www/html' \
               '\n\tServerName {}' \
               '\n\tSSLEngine on \n\tSSLCertificateFile {}{}.crt ' \
               '\n\tSSLCertificateKeyFile {}{}.key' \
               '\n</VirtualHost>\n</IfModule>'.format(domain_name, cert_path, domain_name, cert_path, domain_name)

    with open(ssl_config_file, 'w') as file:
        file.write(contents)

    # Modifying http configuration for https redirection
    apache_http_configuration(None, None, None, True)


# Https Configuration
def apache_https_configuration(proxy_config, auth_config, miscellaneous_headers, email_address, self_signed_cert):
    ssl_stapling_cache = (
        '\n\n\t# The SSL Stapling Cache global parameter'
        '\n\tSSLStaplingCache shmcb:${APACHE_RUN_DIR}/ssl_stapling_cache(128000)'
        '\n'
    )

    # OSCP stapling configuration for our server
    ocsp_stapling_config = (
        '\n\n\t#OSCP Stapling Configuration'
        '\n\tSSLUseStapling on'
        '\n\tSSLStaplingReturnResponderErrors off'
        '\n\tSSLStaplingResponderTimeout 5'
        '\n\n'
    )

    # HSTS configuration
    hsts_config = (
        '\n\n\t# HSTS for 1 year including the subdomains'
        '\n\tHeader always set Strict-Transport-Security "max-age=31536000; includeSubDomains"'
        '\n'
    )

    common_ssl_configuration = proxy_config + miscellaneous_headers + hsts_config

    if self_signed_cert:
        ssl_config_path = '/etc/apache2/sites-available/'
        ssl_config_name = '000-default-minidmz-ssl.conf'
        ssl_config_file = ssl_config_path + ssl_config_name
        apache_self_signed_configuration(ssl_config_file, email_address, settings.DOMAIN_NAME)
        subprocess.check_output(['a2enmod', 'ssl'])
        # Enabling the http virtual host
        subprocess.check_output(['a2ensite', ssl_config_name])
    else:
        ssl_config_file = '/etc/apache2/sites-available/000-default-le-ssl.conf'
        # OSCP stapling configured if certbot is used.
        common_ssl_configuration = common_ssl_configuration + ocsp_stapling_config

    https_config(common_ssl_configuration, auth_config, ssl_config_file)

    # No need to enable OSCP if self signed
    if not self_signed_cert:
        ssl_mod_file = '/etc/apache2/mods-available/ssl.conf'
        settings.backup_file(ssl_mod_file)

        with open(ssl_mod_file, 'r') as file:
            contents = file.readlines()

        if len(contents) == 0:
            print('[ERROR]The {} file has no contents'.format(ssl_mod_file))
            sys.exit()

        with open(ssl_mod_file, 'w') as file:
            for line in contents:
                file.write(line)
                if line.strip() == '<IfModule mod_ssl.c>':
                    file.write(ssl_stapling_cache)


# Returns the list of the authentication module package(s)
# Returns the configuration for the corresponding module
def fetch_authentication_configuration(saml_authentication):
    # CAS Config
    cas_auth_config = ('\n\tCASCookiePath /var/cache/apache2/mod_auth_cas/'
                       '\n\tCASLoginURL ' + settings.CAS_AUTHORIZATION_ENDPOINT +
                       '\n\tCASValidateURL ' + settings.CAS_VALIDATION_ENDPOINT +
                       '\n\n\t<Location />\n\t\tAuthType CAS\n\t\trequire valid-user\n\t</Location>\n'
                       )
    cas_auth_packages = ['libapache2-mod-auth-cas']
    cas_auth_modules = ['auth_cas']

    # SAML auth configuration. Using Shibboleth.
    saml_auth_config = ('\n\n\t<Location />\n\t\tAuthType Shibboleth\n\t\tShibRequireSession On'
                        '\n\t\trequire valid-user\n\t</Location>\n'
                        )
    saml_auth_packages = ['libapache2-mod-shib2']
    saml_auth_modules = ['shib2']

    request_header_config = '\n\tRequestHeader set REMOTE_USER expr=%{REMOTE_USER}\n'

    if not saml_authentication:
        return cas_auth_modules, cas_auth_packages, cas_auth_config + request_header_config
    else:
        return saml_auth_modules, saml_auth_packages, saml_auth_config + request_header_config


def read_saml_configuration():
    config_file_path = Path('/boot/saml_config.json')

    with config_file_path.open('r') as json_data_file:
        data = json.load(json_data_file)

    if not data['sso_entity_id'].strip() or not data['metadata_uri'].strip():
        print('[Error] Missing configuration paramaters in {} file.'.format(config_file_path))
        sys.exit()

    return data['sso_entity_id'].strip(), data['metadata_uri'].strip()


def saml_specific_configuration(domain_name, contact_email):

    sso_entity_id, metadata_uri = read_saml_configuration()

    sibboleth_config_file = '/etc/shibboleth/shibboleth2.xml'

    settings.backup_file(sibboleth_config_file)

    # Entity ID, Breaks if http configuration. TODO: Fix this later
    application_entity_id = 'https://{}/shibboleth'.format(domain_name)

    # Generating certificate for shibboleth
    cert_gen_command = ('openssl req -newkey rsa:4096 -new -x509 -days 3652 -nodes -text '
                        '-out /etc/shibboleth/sp-key.pem -keyout /etc/shibboleth/sp-cert.pem -subj "/C=US/ST=Indiana'
                        '/L=Bloomington/O=Indiana University/'
                        'OU=UITS/CN={}/emailAddress={}"').format(domain_name, contact_email)

    subprocess.check_output(cert_gen_command, shell=True)

    # Setting the application entityID
    subprocess.check_output(['sed', '-i', '--',
                             's|ApplicationDefaults entityID="https://sp.example.org/shibboleth"|'
                             'ApplicationDefaults entityID="{}"|g'.format(application_entity_id),
                             sibboleth_config_file])

    # Setting the SSO entityID
    subprocess.check_output(['sed', '-i', '--',
                             's|SSO entityID="https://idp.example.org/idp/shibboleth"|'
                             'SSO entityID="{}"|g'.format(sso_entity_id),
                             sibboleth_config_file])

    # HTTPS configuration
    subprocess.check_output(['sed', '-i', '--',
                             's|handlerSSL="false"|handlerSSL="true"|g',
                             sibboleth_config_file])
    subprocess.check_output(['sed', '-i', '--',
                             's|cookieProps="http"|cookieProps="https"|g',
                             sibboleth_config_file])

    # Error contact configuration
    subprocess.check_output(['sed', '-i', '--',
                             's|supportContact="root@localhost"|supportContact="{}"|g'.format(contact_email),
                             sibboleth_config_file])

    metadata_value = '<MetadataProvider type="XML" reloadInterval="86400" uri="{}"/>'.format(metadata_uri)

    # Metadata configuration
    sed_command = ('s|<!-- Example of remotely supplied batch of signed metadata. -->|'
                   '<!-- Example of remotely supplied batch of signed metadata. -->{}|g').format(metadata_value)

    subprocess.check_output(['sed', '-i', '--', sed_command, sibboleth_config_file])


# Creating configuration to proxy requests to the tomcat container
def apache_configuration(http_setup, self_signed_cert, email_id, saml):
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
        '\n\tHeader always set X-Xss-Protection "1; mode=block"\n'
    )

    # Authentication module installation command, Authentication module configuration
    auth_modules, auth_packages, auth_config = fetch_authentication_configuration(saml)

    if http_setup:
        apache_http_configuration(proxy_config, auth_config, miscellaneous_headers, False)
    else:
        apache_https_configuration(proxy_config, auth_config, miscellaneous_headers, email_id, self_signed_cert)

    subprocess.call(['apt-get', '-y', 'install'] + auth_packages)

    apache_config_file = '/etc/apache2/apache2.conf'
    settings.backup_file(apache_config_file)

    with open(apache_config_file, 'a') as file:
        file.write(apache_signature_config)

    # Disabling directory browsing
    subprocess.check_output(['sed', '-i', '--',
                             's|Options Indexes FollowSymLinks|Options FollowSymLinks|g',
                             apache_config_file])

    # Enabling modules for proxying, HSTS and CAS
    subprocess.check_output(['a2enmod', 'proxy_http', 'proxy_wstunnel', 'headers'] + auth_modules)

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
    subprocess.check_call('curl -sSL https://get.docker.com | sh', shell=True)
    subprocess.check_output(['systemctl', 'enable', 'docker'])
    subprocess.check_output(['systemctl', 'start', 'docker'])
    subprocess.check_output(['usermod', '-aG', 'docker', 'pi'])


# Downloading our application from our git repository
def guacamole_configuration():
    path = '/home/pi/minidmz'

    if os.path.isdir(path):
        print('Guacamole setup files already exists in {}'.format(path))
        return

    git_command = 'git clone --branch master https://github.com/kausrini/Mini-ScienceDMZ.git {}'.format(path)
    print('Fetching the guacamole setup files from git repository')
    subprocess.check_output(['runuser', '-l', 'pi', '-c', git_command])
    subprocess.check_output(['chmod', '774', path + '/guacamole_setup_files/setup.py'])


def restore_rules():
    file_object = open("/etc/rc.local", "r")
    cont = file_object.readlines()
    cont = cont[:-1]
    file_object.close()

    write_file = open("/etc/rc.local", "w")
    write_file.writelines([item for item in cont])
    write_file.write("sudo /sbin/iptables-restore < /etc/iptables/rules.v4")
    write_file.write("\n")
    write_file.write("sudo /sbin/ip6tables-restore < /etc/iptables/rules.v6")
    write_file.write("\n")
    write_file.write("exit 0" + "\n")    
    write_file.close()


def setup_cronjobs():
    # Update dns after reboot.
    # Update dns every one hour.
    # Start docker containers on boot (Todo Python script for this with proper checks of existence of containers)
    cron_jobs_list = [
        '@reboot docker start sql_container\n',
        '@reboot docker start guacamole_container\n',
        '0 * * * * python /home/pi/minidmz/log_email/send_status.py\n'
    ]

    # Add cronjob if the dynv6 script exists
    if os.path.exists('/etc/dns/dynv6.sh'):
        cron_jobs_list.append('@reboot /etc/dns/dynv6.sh\n0 * * * * /etc/dns/dynv6.sh\n')

    cron_file_name = 'temp_cron'
    file_path = '/tmp/' + cron_file_name

    with open(file_path, 'w') as file_object:
        file_object.write(''.join(cron_jobs_list))

    subprocess.check_output(['crontab', file_path])
    os.remove(file_path)

    if os.path.isfile('/etc/firewall/iptables.sh'):
        # Add firewall rules
        subprocess.check_output(['/etc/firewall/iptables.sh'])

    if not os.path.isfile('/etc/iptables/rules.v4'):
        open('/etc/iptables/rules.v4', 'a').close()
    if not os.path.isfile('/etc/iptables/rules.v6'):
        open('/etc/iptables/rules.v6', 'a').close()

        # Save IPv4 rules
    subprocess.check_output(['su', 'root', '-c', '/sbin/iptables-save >> /etc/iptables/rules.v4'])

    # Save IPv6 rules
    subprocess.check_output(['su', 'root', '-c', '/sbin/ip6tables-save >> /etc/iptables/rules.v6'])

    # These method will make sure that our firewall rules persist on reboot
    restore_rules()


# Rebooting the raspberry pi
def clean_up_setup():
    upgrade_packages()
    print('Rebooting the system in 5 seconds...')
    time.sleep(5)
    subprocess.check_output(['reboot', 'now'])


if __name__ == '__main__':
    arguments = fetch_arguments()
    settings.test_values()
    if not settings.check_internet_connectivity():
        sys.exit(1)
    email = arguments.email
    self_signed = arguments.self
    install_packages(arguments.insecure or self_signed)

    if arguments.perfsonar:
        # Installs perfsonar testpoint on the device
        perfinst.setup_perfsonar()

    isc_dhcp_server_configuration()
    docker_install()
    guacamole_configuration()
    if not arguments.insecure or arguments.saml:
        if email is None:
            sys.stdout.write('\n\nPlease enter your email address : ')
            email = input()
        if not self_signed:
            self_signed = certbot_tls_configuration(email, arguments.testing)
    apache_configuration(arguments.insecure, self_signed, email, arguments.saml)

    if arguments.saml:
        saml_specific_configuration(settings.DOMAIN_NAME, email)

    setup_cronjobs()
    clean_up_setup()
