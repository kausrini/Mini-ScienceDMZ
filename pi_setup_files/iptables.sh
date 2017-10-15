#!/bin/bash

#IPV4 RULES

# Flush existing Input and Output policy
iptables -F INPUT
iptables -F OUTPUT

# Default policy for Input and Output
iptables -P OUTPUT  ACCEPT
iptables -P INPUT  DROP

# Allows all loopback (lo0) traffic and drop all traffic to 127/8 that doesn't use lo0
iptables -A INPUT -i lo -j ACCEPT
iptables -A INPUT ! -i lo -d 127.0.0.0/8 -j REJECT

# Accepts all established inbound connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allows HTTP and HTTPS connections from anywhere
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow SSH connections 
iptables -A INPUT -p tcp -m state --state NEW --dport 22 -j ACCEPT

# Allow DHCP Requests through
iptables  -A  INPUT -i eth0 -p udp --dport 67:68 --sport 67:68 -j ACCEPT

# Allow ping
iptables -A INPUT -p icmp -m icmp --icmp-type 8 -j ACCEPT

# log iptables denied calls (access via 'dmesg' command)
iptables -A INPUT -m limit --limit 5/min -j LOG --log-prefix "iptables denied: " --log-level 7


#IPV6 RULES

# Flush chains
ip6tables -F INPUT
ip6tables -F FORWARD
ip6tables -F OUTPUT

# Set up default policies
ip6tables -P INPUT DROP
ip6tables -P FORWARD DROP
ip6tables -P OUTPUT ACCEPT

# Allow localhost traffic.
ip6tables -A INPUT -s ::1 -d ::1 -j ACCEPT

# Allow some ICMPv6 types in the INPUT chain
# Using ICMPv6 type names to be clear.
ip6tables -A INPUT -p icmpv6 --icmpv6-type destination-unreachable -j ACCEPT
ip6tables -A INPUT -p icmpv6 --icmpv6-type packet-too-big -j ACCEPT
ip6tables -A INPUT -p icmpv6 --icmpv6-type time-exceeded -j ACCEPT
ip6tables -A INPUT -p icmpv6 --icmpv6-type parameter-problem -j ACCEPT

# Allow some other types in the INPUT chain, but rate limit.
ip6tables -A INPUT -p icmpv6 --icmpv6-type echo-request -m limit --limit 900/min -j ACCEPT
ip6tables -A INPUT -p icmpv6 --icmpv6-type echo-reply -m limit --limit 900/min -j ACCEPT

# Allow others ICMPv6 types but only if the hop limit field is 255.
ip6tables -A INPUT -p icmpv6 --icmpv6-type router-advertisement -m hl --hl-eq 255 -j ACCEPT
ip6tables -A INPUT -p icmpv6 --icmpv6-type neighbor-solicitation -m hl --hl-eq 255 -j ACCEPT
ip6tables -A INPUT -p icmpv6 --icmpv6-type neighbor-advertisement -m hl --hl-eq 255 -j ACCEPT
ip6tables -A INPUT -p icmpv6 --icmpv6-type redirect -m hl --hl-eq 255 -j ACCEPT

# When there isn't a match, the default policy (DROP) will be applied.
# To be sure, drop all other ICMPv6 types.
# We're dropping enough icmpv6 types to break RFC compliance.
ip6tables -A INPUT -p icmpv6 -j LOG --log-prefix "Dropped ICMPv6"
ip6tables -A INPUT -p icmpv6 -j DROP

# Accepts all established inbound connections
ip6tables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allows HTTP and HTTPS connections from anywhere
ip6tables -A INPUT -p tcp --dport 80 -j ACCEPT
ip6tables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow SSH connections 
ip6tables -A INPUT -p tcp -m state --state NEW --dport 22 -j ACCEPT

