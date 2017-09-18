import argparse
import subprocess
import getpass
import time


# Obtain command line arguments
def fetch_argument():
    parser = argparse.ArgumentParser(description='Sets up the Raspberry Pi')
    parser.add_argument('-u', '--username',
                        help='DynDNS Username to connect to the Dyn Dns network',
                        required=True
                        )

    dyn_username = parser.parse_args().username

    while True:
        dyn_password = getpass.getpass('DynDNS Password : ')
        verify_dyn_password = getpass.getpass('Re-enter DynDNS Password : ')

        if dyn_password == verify_dyn_password:
            break
        else:
            print("[Error] The passwords do not match. Please enter again.")

    return dyn_username, dyn_password


# Installs all required packages for our application
def install_packages():
    packages = ['dnsmasq', 'ddclient', 'git','apache2']

    print('Upgrading existing packages')
    subprocess.call(['apt-get', 'update'])
    subprocess.call(['apt-get', '-y', 'upgrade'])
    print('Installing the following packages {}'.format(", ".join(packages)))
    subprocess.call(['sudo', 'DEBIAN_FRONTEND=noninteractive', 'apt-get', '-y', 'install'] + packages)


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


# Creating the Dyn Dns configuration for dynamic DNS
def dyn_dns_configuration(dyn_username, dyn_password):
    dyn_dns_config = (
        "\nprotocol=dyndns2\n"
        "use=web, web=checkip.dyndns.com, web-skip='IP Address'\n"
        "server=members.dyndns.org\n"
        "login={}\n"
        "password={}\n"
        "poc1.dyndns-at-work.com\n"
    ).format(dyn_username, dyn_password)

    print('Adding the Dynamic DNS configuration to /etc/ddclient.conf file')
    with open('/etc/ddclient.conf', 'a') as file:
        file.write(dyn_dns_config)


# Creating configuration to proxy requests to the tomcat container
def reverse_proxy_configuration():
    print("Creating the Reverse Proxy Configuration")

    proxy_config = (
        '\n<Location /guacamole/>\n'
        '\tOrder allow,deny\n\tAllow from all\n'
        '\tProxyPass http://poc1.dyndns-at-work.com:8080/guacamole/ flushpackets=on\n'
        '\tProxyPassReverse http://poc1.dyndns-at-work.com:8080/guacamole/\n'
        '</Location>\n'
        '\n<Location /guacamole/websocket-tunnel>\n'
        '\tOrder allow,deny\n\tAllow from all\n'
        '\tProxyPass ws://poc1.dyndns-at-work.com:8080/guacamole/websocket-tunnel\n'
        '\tProxyPassReverse ws://poc1.dyndns-at-work.com:8080/guacamole/websocket-tunnel\n'
        '</Location>\n'
    )

    subprocess.check_output(['a2enmod','proxy_http'])
    subprocess.check_output(['a2enmod', 'proxy_wstunnel'])

    with open('/etc/apache2/sites-available/000-default.conf', 'w') as file:
        file.write(proxy_config)


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
    print('Fetching the guacamole setup files from git repository')
    subprocess.call(['git', 'clone', 'https://github.com/kausrini/Mini-ScienceDMZ.git', path])
    subprocess.check_output(['chown','-R', 'pi', path])


# Rebooting the raspberry pi
def clean_up_setup():
    print('Rebooting the system in 5 seconds...')
    time.sleep(5)
    subprocess.check_output(['reboot', 'now'])


if __name__ == '__main__':
    username, password = fetch_argument()
    install_packages()
    dhcp_server_configuration()
    dyn_dns_configuration(username, password)
    docker_install()
    guacamole_configuration()
    clean_up_setup()
