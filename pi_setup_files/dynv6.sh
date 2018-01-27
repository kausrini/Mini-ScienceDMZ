#!/bin/sh -e
token="YOUR_DYNV6_TOKEN_HERE"
hostname="YOUR_DOMAIN_NAME_HERE"
device="YOUR_NETWORK_DEVICE_NAME_HERE"

if [ "$token" = "YOUR_DYNV6_TOKEN_HERE" ]; then
  echo "[ERROR] Valid token is missing in the dynv6 script"
  exit 0 
fi


if [ -z "$hostname" ]; then
  echo "[ERROR] Domain name is missing in the dynv6 script"
  exit 0
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
$bin "http://ipv4.dynv6.com/api/update?hostname=$hostname&ipv4=auto&token=$token"

if [ -z "$address" ]; then
  echo "no IPv6 address found"
  exit 0
fi

# address with netmask
current=$address/$netmask

# Update ipv6 address with dynv6 service
$bin "http://dynv6.com/api/update?hostname=$hostname&ipv6=$current&token=$token" 
