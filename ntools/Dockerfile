# ===== ベースステージ（updateと必要ライブラリのインストール） =====

#
# net-toolsイメージをベースにする
# https://github.com/rtsp/docker-net-tools
#

# CiscoのMIBファイルを追加したい

FROM net-tools:1.0.0 AS base

ENV DEBIAN_FRONTEND=noninteractive

ENV TZ=Asia/Tokyo

# ENV LANG=ja_JP.UTF-8
ENV LANG=en_US.UTF-8

ENV WORKING_DIRECTORY=/var/tmp/build

# ARGは --build-arg で変更可能
ARG HOSTNAME=ntools

# start.shでホスト名を設定するための環境変数
ENV HOSTNAME=${HOSTNAME}

RUN <<EOF

cd ${WORKING_DIRECTORY}

apt update
apt upgrade -y

apt-get update && \
  apt-get upgrade -y && \
  apt-get install -y --no-install-recommends \
  bash iproute2 iputils-ping net-tools mtr-tiny iperf3 traceroute fping \
  sensible-utils curl telnet netcat-openbsd socat snmp termshark \
  openssh-client vim nano less jq yq httpie procps dnsutils bash dhcping nmap && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/* # buildkit



# install prerequisites
apt install -y --no-install-recommends \
    wget \
    curl \
    gnupg2 \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gosu \
    supervisor \
    snmp \
    snmp-mibs-downloader \
    git

# Install utilities
apt install -y --no-install-recommends vim
apt install -y --no-install-recommends nload
apt install -y --no-install-recommends ethtool

#
# Install snmpd (should run in start.sh)
#
apt install -y --no-install-recommends snmpd

echo "" >> /etc/snmp/snmpd.conf
echo "# agentx" >> /etc/snmp/snmpd.conf
echo "agentxsocket /var/agentx/master" >> /etc/snmp/snmpd.conf
echo "agentxperms 777 777" >> /etc/snmp/snmpd.conf

sed -i 's/^rocommunity  public default -V systemonly$/rocommunity  public default/' /etc/snmp/snmpd.conf
sed -i 's/^rocommunity6 public default -V systemonly$/rocommunity6 public default/' /etc/snmp/snmpd.conf
sed -i 's/^agentaddress  127.0.0.1,[::1]$/agentAddress 0.0.0.0/' /etc/snmp/snmpd.conf
sed -i 's/^agentaddress  127/#&/' /etc/snmp/snmpd.conf
echo "agentaddress udp:161,udp6:[::1]:161" >> /etc/snmp/snmpd.conf

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
