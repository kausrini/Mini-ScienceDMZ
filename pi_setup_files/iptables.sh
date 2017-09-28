#!/bin/bash

# Default policy for Input and Output
iptables -P OUTPUT  ACCEPT
iptables -P INPUT  DROP

# Allows all loopback (lo0) traffic and drop all traffic to 127/8 that doesn't use lo0
iptables -A INPUT -i lo -j ACCEPT
iptables -A INPUT ! -i lo -d 127.0.0.0/8 -j REJECT

# Accepts all established inbound connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT


# Allows HTTP and HTTPS connections from anywhere (Will be blocking 8080 in future after setting up reverse proxy)
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
iptables -A INPUT -p tcp --dport 8080 -j ACCEPT

# Allow SSH connections 
iptables -A INPUT -p tcp -m state --state NEW --dport 22 -j ACCEPT

# Allow DHCP Requests through
iptables  -A  INPUT -i eth0 -p udp --dport 67:68 --sport 67:68 -j ACCEPT

# Allow ping
iptables -A INPUT -p icmp -m icmp --icmp-type 8 -j ACCEPT

# log iptables denied calls (access via 'dmesg' command)
iptables -A INPUT -m limit --limit 5/min -j LOG --log-prefix "iptables denied: " --log-level 7