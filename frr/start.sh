#!/bin/bash

CONFIG=/etc/frr/frr.conf
BOOT=/config/boot.sh
PROTOCOLS=/config/protocols

# Not needed for Docker
# for iface in /sys/class/net/*; do
#   iface_name=$(basename "$iface")
#   if /usr/sbin/ethtool "$iface_name" &>/dev/null; then
#     /usr/sbin/ethtool -K "$iface_name" tx off
#   fi
# done

#
# run snmpd in the background
#
if [ -x /usr/sbin/snmpd ]; then
    # /usr/sbin/snmpd -Lsd
    /usr/sbin/snmpd -LS 5 d -Lf /dev/null
fi

#
# run sshd in the background
#
if [ -x /usr/sbin/sshd ]; then
    /usr/sbin/sshd -D
fi

# enable the requested protocols
while IFS= read -r line; do
    line=$(echo "$line" | xargs) # no whitespace
    if [[ -n "$line" && ! "$line" =~ ^# ]]; then
        sed -r -e "s/^(${line}=)no$/\1yes/" -i /etc/frr/daemons
    fi
done <"$PROTOCOLS"

# Not needed to copy the day0 config as it's mounted directly to /etc/frr/frr.conf
#if [ -f $CONFIG ]; then
#    cp $CONFIG /etc/frr/frr.conf
#fi

# set the hostname from the provided config if it's there
if [ -f $CONFIG ]; then
    hostname_value="router"
    if grep -q "^hostname" $CONFIG; then
        hostname_value=$(awk '/^hostname/ {print $2}' $CONFIG)
    fi
    hostname $hostname_value
fi

# exit if frrinit.sh is not found
if [ ! -f /usr/lib/frr/frrinit.sh ]; then
    echo "/usr/lib/frr/frrinit.sh not found. Exiting."
    exit 1
fi

/usr/lib/frr/frrinit.sh start

echo "READY" >/dev/console

trap '' INT TSTP
while true; do
    /usr/bin/vtysh
done
