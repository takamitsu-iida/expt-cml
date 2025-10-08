# ===== ベースステージ（updateと必要ライブラリのインストール） =====

# CiscoのMIBファイルを追加したい

FROM ubuntu:24.04 AS base

ENV TZ=Asia/Tokyo

# ENV LANG=ja_JP.UTF-8
ENV LANG=en_US.UTF-8

# ARGは --build-arg で変更可能
ARG HOSTNAME=ntools

# start.shでホスト名を設定するための環境変数
ENV HOSTNAME=${HOSTNAME}

ENV WORKING_DIRECTORY=/var/tmp/build


# パッケージごとにインストールしてエラーを切り分け
RUN apt update && apt upgrade -y
RUN apt install -y --no-install-recommends iproute2 || echo "FAILED: iproute2"
RUN apt install -y --no-install-recommends iputils-ping || echo "FAILED: iputils-ping"
RUN apt install -y --no-install-recommends net-tools || echo "FAILED: net-tools"
RUN apt install -y --no-install-recommends mtr-tiny || echo "FAILED: mtr-tiny"
RUN apt install -y --no-install-recommends traceroute || echo "FAILED: traceroute"
RUN apt install -y --no-install-recommends fping || echo "FAILED: fping"
RUN apt install -y --no-install-recommends telnet || echo "FAILED: telnet"
RUN apt install -y --no-install-recommends netcat-openbsd || echo "FAILED: netcat-openbsd"
RUN apt install -y --no-install-recommends socat || echo "FAILED: socat"
RUN apt install -y --no-install-recommends snmp || echo "FAILED: snmp"
RUN apt install -y --no-install-recommends snmp-mibs-downloader || echo "FAILED: snmp-mibs-downloader"
RUN apt install -y --no-install-recommends termshark || echo "FAILED: termshark"
RUN apt install -y --no-install-recommends openssh-client || echo "FAILED: openssh-client"
RUN apt install -y --no-install-recommends openssh-server || echo "FAILED: openssh-server"
RUN apt install -y --no-install-recommends less || echo "FAILED: less"
RUN apt install -y --no-install-recommends jq || echo "FAILED: jq"
RUN apt install -y --no-install-recommends yq || echo "FAILED: yq"
RUN apt install -y --no-install-recommends httpie || echo "FAILED: httpie"
RUN apt install -y --no-install-recommends procps || echo "FAILED: procps"
RUN apt install -y --no-install-recommends dnsutils || echo "FAILED: dnsutils"
RUN apt install -y --no-install-recommends bash || echo "FAILED: bash"
RUN apt install -y --no-install-recommends dhcping || echo "FAILED: dhcping"
RUN apt install -y --no-install-recommends nmap || echo "FAILED: nmap"
RUN apt install -y --no-install-recommends wget || echo "FAILED: wget"
RUN apt install -y --no-install-recommends curl || echo "FAILED: curl"
RUN apt install -y --no-install-recommends git || echo "FAILED: git"
RUN apt install -y --no-install-recommends vim || echo "FAILED: vim"
RUN apt install -y --no-install-recommends nano || echo "FAILED: nano"
RUN apt install -y --no-install-recommends ethtool || echo "FAILED: ethtool"
RUN apt install -y --no-install-recommends python3 || echo "FAILED: python3"
RUN apt install -y --no-install-recommends python3-pip || echo "FAILED: python3-pip"
RUN apt install -y --no-install-recommends python3-venv || echo "FAILED: python3-venv"
RUN apt install -y --no-install-recommends direnv || echo "FAILED: direnv"

RUN <<EOF

cd ${WORKING_DIRECTORY}

apt update
apt upgrade -y
apt install -y --no-install-recommends \
  iproute2 \
  iputils-ping \
  net-tools \
  mtr-tiny \
  traceroute \
  fping \
  telnet \
  netcat-openbsd \
  socat \
  snmp \
  snmp-mibs-downloader \
  termshark \
  openssh-client \
  openssh-server \
  less \
  jq \
  yq \
  httpie \
  procps \
  dnsutils \
  bash \
  dhcping \
  nmap
  wget \
  curl \
  git \
  vim \
  nano \
  ethtool \
  python3 \
  python3-pip \
  python3-venv \
  direnv

pip3 install --upgrade pip
pip3 install --no-cache-dir \
    requests \
    flask \
    pysnmp \
    pysnmp-mibs \
    scapy \
    netaddr \
    paramiko \
    textfsm \
    jinja2 \
    ntc-templates \
    virl2_client[pyats]==2.9 \

#
# sshd (should run in start.sh)
#
sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
grep -q '^PermitRootLogin yes' /etc/ssh/sshd_config || echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config

sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
grep -q '^PasswordAuthentication yes' /etc/ssh/sshd_config || echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config

sed -i 's/UsePAM yes/UsePAM no/' /etc/ssh/sshd_config
grep -q '^UsePAM no' /etc/ssh/sshd_config || echo 'UsePAM no' >> /etc/ssh/sshd_config

sed -i 's/#PermitEmptyPasswords no/PermitEmptyPasswords yes/' /etc/ssh/sshd_config
grep -q '^PermitEmptyPasswords yes' /etc/ssh/sshd_config || echo 'PermitEmptyPasswords yes' >> /etc/ssh/sshd_config

# username and password should be changed after container started, see start.sh

#
# direnvのhookを.bashrcに追加
#
echo '\n# direnv' >> /etc/bash.bashrc
echo 'eval "$(direnv hook bash)"' >> /etc/bash.bashrc
echo 'export EDITOR=vi' >> /etc/bash.bashrc


# --- Clean up ---
apt autoremove -y
apt clean
cd /
rm -rf /var/lib/apt/lists/*
rm -rf /var/lib/cache/*
rm -rf ${WORKING_DIRECTORY}

unset WORKING_DIRECTORY

cd /root
git clone https://github.com/upa/deadman.git

EOF

COPY --chmod=0755 start.sh /

ENTRYPOINT [ "/start.sh" ]
