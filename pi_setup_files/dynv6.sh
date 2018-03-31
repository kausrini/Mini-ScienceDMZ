#!/bin/sh -e
token="YOUR_DYNV6_TOKEN_HERE"
hostname="YOUR_DOMAIN_NAME_HERE"
device="YOUR_NETWORK_DEVICE_NAME_HERE"

if [ "$token" = "YOUR_DYNV6_TOKEN_HERE" ]; then
  echo "[ERROR] Valid token is missing in the dynv6 script"
  exit 1 
fi

if [ "$hostname" = "YOUR_DOMAIN_NAME_HERE" ]; then
  echo "[ERROR] Valid domain name is missing in the dynv6 script"
  exit 1 
fi

if [ "$device" = "YOUR_NETWORK_DEVICE_NAME_HERE" ]; then
  echo "[ERROR] Valid network device is missing in the dynv6 script"
  exit 1 
fi

if [ -z "$netmask" ]; then
  netmask=128 
fi

if [ -n "$device" ]; then
  device="dev $device"
fi

address=$(ip -6 addr list scope global $device | grep -v " fd" | sed -n 's/.*inet6 \([0-9a-f:]\+\).*/\1/p' | head -n 1)

if [ -e /usr/bin/curl ]; then
  bin="curl -fsS"
elif [ -e /usr/bin/wget ]; then
  bin="wget -O-"
else
  echo "neither curl nor wget found"
  exit 0
fi

# Update ipv4 address with dynv6 service
$bin "https://ipv4.dynv6.com/api/update?hostname=$hostname&ipv4=auto&token=$token"

if [ -z "$address" ]; then
  echo "no IPv6 address found"
  echo "Sending auto as dynv6 ipv6 address"
  current="auto"
else
  # address with netmask
  current=$address/$netmask  
fi

# Update ipv6 address with dynv6 service
$bin "https://dynv6.com/api/update?hostname=$hostname&ipv6=$current&token=$token" 
