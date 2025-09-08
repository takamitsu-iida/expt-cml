# ===== ベースステージ（updateと必要ライブラリのインストール） =====
FROM ubuntu:24.04 AS base

ENV TZ=Asia/Tokyo
ENV LANG=ja_JP.UTF-8

RUN <<EOF

apt update
apt upgrade -y

# install prerequisites
apt install -y \
    wget \
    curl \
    gnupg \
    software-properties-common \
    apt-transport-https \
    supervisor \
    ca-certificates \
    inotify-tools \

# Clean up
apt remove -y
apt autoremove -y
apt clean
rm -rf /var/lib/apt/lists/*
rm -rf /var/lib/cache/*

EOF

# ===== TIG ビルドステージ =====
FROM base AS builder

RUN <<EOF

# --- Install InfluxDB 1.x ---
wget -qO- https://repos.influxdata.com/influxdb.key | gpg --dearmor | tee /etc/apt/trusted.gpg.d/influxdb.gpg > /dev/null
echo "deb https://repos.influxdata.com/ubuntu jammy stable" | tee /etc/apt/sources.list.d/influxdb.list
apt update
apt install -y influxdb

# Create InfluxDB directories
mkdir -p /var/lib/influxdb /var/log/influxdb
chown -R influxdb:influxdb /var/lib/influxdb
chmod -R 755 /var/lib/influxdb

# --- Install Telegraf ---
wget -qO- https://repos.influxdata.com/influxdb.key | gpg --dearmor | tee /etc/apt/trusted.gpg.d/influxdb.gpg > /dev/null
echo "deb https://repos.influxdata.com/ubuntu jammy stable" | tee /etc/apt/sources.list.d/telegraf.list
apt update
apt install -y telegraf

# --- Install Grafana ---
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | tee /etc/apt/trusted.gpg.d/grafana.gpg > /dev/null
echo "deb https://apt.grafana.com stable main" | tee /etc/apt/sources.list.d/grafana.list
apt update
apt install -y grafana

chown -R grafana:grafana /var/lib/grafana
chmod -R 755 /var/lib/grafana

# Create mountpoint directory
mkdir /config

# Clean up
apt remove -y
apt autoremove -y
apt clean
rm -rf /var/lib/apt/lists/*
rm -rf /var/lib/cache/*

EOF

# Expose ports
# EXPOSE 8086 # InfluxDB
# EXPOSE 3000 # Grafana

# Volume for data persistence (optional, but recommended)
# VOLUME /var/lib/influxdb
# VOLUME /var/lib/grafana

COPY influxdb.conf /etc/influxdb/influxdb.conf
COPY telegraf.conf /etc/telegraf/telegraf.conf

# Grafanaのデフォルト設定は`/etc/grafana/grafana.ini`。
# 環境変数で多くの設定を上書き可能。
# ADMINユーザーとパスワードは環境変数で設定可能だが、ここではSupervisordのスタートスクリプトで設定することにする
# COPY grafana.ini /etc/grafana/grafana.ini # カスタム設定ファイルがあれば

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf


# Startup command
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
