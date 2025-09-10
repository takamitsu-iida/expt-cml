# ===== ベースステージ（updateと必要ライブラリのインストール） =====
FROM ubuntu:24.04 AS base

ENV TZ=Asia/Tokyo
ENV LANG=ja_JP.UTF-8

# ARGは --build-arg で変更可能
ARG HOSTNAME=tig

ARG ORG=my_org
ARG BUCKET=my_bucket
ARG TOKEN

# InfluxDB と Grafana の管理者ユーザーとパスワード
# パスワードは最低8文字
ARG ADMIN_USER=admin
ARG ADMIN_PASSWORD=password

# ARGをそのまま環境変数にしておく
ENV ORG=${ORG}
ENV BUCKET=${BUCKET}
ENV TOKEN=${TOKEN}
ENV ADMIN_USER=${ADMIN_USER}
ENV ADMIN_PASSWORD=${ADMIN_PASSWORD}

# InfluxDB 環境変数
# start.shで初期化するときに使用する
ENV DOCKER_INFLUXDB_INIT_ORG=${ORG}
ENV DOCKER_INFLUXDB_INIT_BUCKET=${BUCKET}
ENV DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=${TOKEN}
ENV DOCKER_INFLUXDB_INIT_USERNAME=${ADMIN_USER}
ENV DOCKER_INFLUXDB_INIT_PASSWORD=${ADMIN_PASSWORD}

# Grafana 環境変数
ENV GF_SECURITY_ADMIN_USER=${ADMIN_USER}
ENV GF_SECURITY_ADMIN_PASSWORD=${ADMIN_PASSWORD}

# start.shでホスト名を設定するための環境変数
ENV HOSTNAME=${HOSTNAME}

RUN <<EOF

apt update
apt upgrade -y

# install prerequisites
apt install -y --no-install-recommends \
    wget \
    curl \
    gnupg2 \
    software-properties-common \
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
apt autoremove -y
apt clean
rm -rf /var/lib/apt/lists/*
rm -rf /var/lib/cache/*

EOF

# ===== TIG ビルドステージ =====
FROM base AS builder

ENV WORKING_DIRECTORY=/var/tmp/build

RUN <<EOF

mkdir -p ${WORKING_DIRECTORY}
cd ${WORKING_DIRECTORY}

# --- Install Telegraf ---
wget -qO- https://repos.influxdata.com/influxdb.key | gpg --dearmor | tee /usr/share/keyrings/influxdb-archive-keyring.gpg > /dev/null
echo "deb [signed-by=/usr/share/keyrings/influxdb-archive-keyring.gpg] https://repos.influxdata.com/ubuntu jammy stable" | tee /etc/apt/sources.list.d/influxdata.list

apt update
apt install -y --no-install-recommends telegraf


# --- Install InfluxDB 2.x ---

# インストール方法は公式ドキュメント参照
# https://docs.influxdata.com/influxdb/v2/install/
# influxDBとinflux CLIは別パッケージなので両方インストールする
# systemdで起動するわけではないので、tar.gzをダウンロードして展開する

# Use curl to download the amd64 binary.
curl --location -O https://download.influxdata.com/influxdb/releases/v2.7.12/influxdb2-2.7.12_linux_amd64.tar.gz
tar xvzf ./influxdb2-2.7.12_linux_amd64.tar.gz

cp ./influxdb2-2.7.12/usr/bin/influxd /usr/bin/

mkdir -p /var/lib/influxdb2
# chown -R influxdb:influxdb /var/lib/influxdb2
# chmod -R 755 /var/lib/influxdb2


# Install the influx CLI
# https://docs.influxdata.com/influxdb/v2/tools/influx-cli/?t=Linux

curl --location -O https://dl.influxdata.com/influxdb/releases/influxdb2-client-2.7.5-linux-amd64.tar.gz
tar xvzf ./influxdb2-client-2.7.5-linux-amd64.tar.gz

cp ./influx /usr/bin/


# --- Install Grafana ---
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | tee /etc/apt/trusted.gpg.d/grafana.gpg > /dev/null
echo "deb https://apt.grafana.com stable main" | tee /etc/apt/sources.list.d/grafana.list

apt update
apt install -y --no-install-recommends grafana

chown -R grafana:grafana /var/lib/grafana
chmod -R 755 /var/lib/grafana


# --- Clean up ---
apt autoremove -y
apt clean
cd /
rm -rf /var/lib/apt/lists/*
rm -rf /var/lib/cache/*
rm -rf ${WORKING_DIRECTORY}
unset WORKING_DIRECTORY

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

COPY --chmod=0755 start.sh /

ENTRYPOINT [ "/start.sh" ]
