#!/bin/bash

hostname ${HOSTNAME}

#
# run sshd in the background
#

if [ -x /usr/sbin/sshd ]; then
    if [ ! -f /etc/ssh/ssh_host_rsa_key ]; then
        ssh-keygen -A
    fi
    mkdir -p /var/run/sshd
    # echo "cisco:cisco" | chpasswd
    # echo "root:cisco" | chpasswd
    passwd -d root
    /usr/sbin/sshd -E /var/log/sshd.log
fi

echo "READY" >/dev/console

# コンテナが終了しないように bash -i をループさせます。
trap '' INT TSTP
while true; do
    bash -i
done
