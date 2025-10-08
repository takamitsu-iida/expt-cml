# ===== ベースステージ（updateと必要ライブラリのインストール） =====

# CiscoのMIBファイルを追加したい

FROM ubuntu22.04 AS base

ENV TZ=Asia/Tokyo

# ENV LANG=ja_JP.UTF-8
ENV LANG=en_US.UTF-8

# ARGは --build-arg で変更可能
ARG HOSTNAME=ntools

# start.shでホスト名を設定するための環境変数
ENV HOSTNAME=${HOSTNAME}

ENV WORKING_DIRECTORY=/var/tmp/build

RUN <<EOF

cd ${WORKING_DIRECTORY}

apt update
apt upgrade -y

apt install -y --no-install-recommends \
  iproute2 \
  iputils-ping \
  net-tools \
  mtr-tiny \
  iperf3 \
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
