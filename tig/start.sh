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

#
# run supervisord
#

/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf

#
# run influxdb initial setup
#

# InfluxDBの起動を待つ
echo "Waiting for InfluxDB to start..."
until curl -sI http://localhost:8086/ping 2>&1 | grep -q 'HTTP/1.1 204 No Content'; do
    sleep 3
done
echo "InfluxDB started."


SETUP_MARKER="# SETUP_DONE"
INFLUX_CONF="/etc/influxdb/influxdb.conf"

# 初期セットアップ済みか判定
if ! grep -q "$SETUP_MARKER" "$INFLUX_CONF"; then

    # 環境変数が設定されているか確認
    if  [ -z "$DOCKER_INFLUXDB_INIT_ORG" ] || \
        [ -z "$DOCKER_INFLUXDB_INIT_BUCKET" ] || \
        [ -z "$DOCKER_INFLUXDB_INIT_ADMIN_TOKEN" ] || \
        [ -z "$DOCKER_INFLUXDB_INIT_USERNAME" ] || \
        [ -z "$DOCKER_INFLUXDB_INIT_PASSWORD" ]; then
        echo "One or more InfluxDB initial setup environment variables are not set."
        echo "Skipping initial setup."
    else
        echo "Performing InfluxDB initial setup..."
        influx setup \
            --org "$DOCKER_INFLUXDB_INIT_ORG" \
            --bucket "$DOCKER_INFLUXDB_INIT_BUCKET" \
            --username "$DOCKER_INFLUXDB_INIT_USERNAME" \
            --password "$DOCKER_INFLUXDB_INIT_PASSWORD" \
            --token "$DOCKER_INFLUXDB_INIT_ADMIN_TOKEN" \
            --force
        echo "InfluxDB initial setup completed."

        # 判定用コメントを追加
        echo "" >> "$INFLUX_CONF"
        echo "$SETUP_MARKER" >> "$INFLUX_CONF"
    fi
else
    echo "InfluxDB already initialized. Skipping setup."
fi


echo "READY" >/dev/console

trap '' INT TSTP
while true; do
    bash -i
done
