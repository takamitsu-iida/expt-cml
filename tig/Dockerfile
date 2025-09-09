# ===== ベースステージ（updateと必要ライブラリのインストール） =====
FROM ubuntu:24.04 AS base

ENV TZ=Asia/Tokyo
ENV LANG=ja_JP.UTF-8

# --build-arg で変更可能なデフォルト値
ARG HOSTNAME=tig
ENV HOSTNAME=${HOSTNAME}

ARG BUCKET=my_bucket
ENV BUCKET=${BUCKET}

ARG ORG=my_org
ENV ORG=${ORG}

# TOKENは自動生成した適当な32桁の文字列 (head /dev/urandom | tr -dc A-Za-z0-9 | head -c 32)
ARG TOKEN=DaW2vgcbGpAHJCFiEpYYF61dBfXD7AMk
ENV TOKEN=${TOKEN}

ARG ADMIN_USER=admin
ENV ADMIN_USER=${ADMIN_USER}

ARG ADMIN_PASSWORD=admin
ENV ADMIN_PASSWORD=${ADMIN_PASSWORD}

ENV GF_SECURITY_ADMIN_USER=${ADMIN_USER}
ENV GF_SECURITY_ADMIN_PASSWORD=${ADMIN_PASSWORD}


RUN <<EOF

apt update
apt upgrade -y

# install prerequisites
apt install -y --no-install-recommends \
    wget \
    curl \
    gnupg \
    apt-transport-https \
    supervisor \
    ca-certificates

#
# add sshd (should run in start.sh)
#
apt install -y --no-install-recommends openssh-server

sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
grep -q '^PermitRootLogin yes' /etc/ssh/sshd_config || echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config

sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
grep -q '^PasswordAuthentication yes' /etc/ssh/sshd_config || echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config

sed -i 's/UsePAM yes/UsePAM no/' /etc/ssh/sshd_config
grep -q '^UsePAM no' /etc/ssh/sshd_config || echo 'UsePAM no' >> /etc/ssh/sshd_config

sed -i 's/#PermitEmptyPasswords no/PermitEmptyPasswords yes/' /etc/ssh/sshd_config
grep -q '^PermitEmptyPasswords yes' /etc/ssh/sshd_config || echo 'PermitEmptyPasswords yes' >> /etc/ssh/sshd_config

# username and password should be changed after container started, see start.sh


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

# --- Install InfluxDB 2.x ---
wget -qO- https://repos.influxdata.com/influxdb.key | gpg --dearmor | tee /etc/apt/trusted.gpg.d/influxdb.gpg > /dev/null
echo "deb https://repos.influxdata.com/ubuntu jammy stable" | tee /etc/apt/sources.list.d/influxdb.list

apt update
apt install -y --no-install-recommends influxdb2

mkdir -p /var/lib/influxdb2 /var/log/influxdb2
chown -R influxdb:influxdb /var/lib/influxdb2
chmod -R 755 /var/lib/influxdb2


# --- Install Telegraf ---
wget -qO- https://repos.influxdata.com/influxdb.key | gpg --dearmor | tee /etc/apt/trusted.gpg.d/influxdb.gpg > /dev/null
echo "deb https://repos.influxdata.com/ubuntu jammy stable" | tee /etc/apt/sources.list.d/telegraf.list

apt update
apt install -y --no-install-recommends telegraf


# --- Install Grafana ---
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | tee /etc/apt/trusted.gpg.d/grafana.gpg > /dev/null
echo "deb https://apt.grafana.com stable main" | tee /etc/apt/sources.list.d/grafana.list

apt update
apt install -y --no-install-recommends grafana

chown -R grafana:grafana /var/lib/grafana
chmod -R 755 /var/lib/grafana


# --- Clean up ---
apt remove -y
apt autoremove -y
apt clean
rm -rf /var/lib/apt/lists/*
rm -rf /var/lib/cache/*

# Create mountpoint directory
mkdir /config

EOF

# Expose ports
# EXPOSE 8086 # InfluxDB
# EXPOSE 3000 # Grafana

# Volume for data persistence (optional, but recommended)
# VOLUME /var/lib/influxdb
# VOLUME /var/lib/grafana

COPY cfg/influxdb.conf /etc/influxdb/influxdb.conf
COPY cfg/telegraf.conf /etc/telegraf/telegraf.conf
COPY cfg/grafana.ini /etc/grafana/grafana.ini
COPY cfg/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

COPY start.sh /

ENTRYPOINT [ "/start.sh" ]
