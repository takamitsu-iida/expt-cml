# Dockerfile for building FRRouting (FRR) on Ubuntu 24.04

# ===== ベースステージ（updateと必要ライブラリのインストール） =====
FROM ubuntu:24.04 AS base

ENV TZ=Asia/Tokyo
ENV LANG=ja_JP.UTF-8

RUN <<EOF

apt update
apt upgrade -y

# install prerequisites
apt install -y --no-install-recommends \
    git autoconf automake libtool make libreadline-dev texinfo \
    pkg-config libpam0g-dev libjson-c-dev bison flex \
    libc-ares-dev python3-dev python3-sphinx \
    install-info build-essential libsnmp-dev perl \
    libcap-dev libelf-dev libunwind-dev \
    protobuf-c-compiler libprotobuf-c-dev

# Install libyang build requirements
apt install -y --no-install-recommends cmake libpcre2-dev

# Install GRPC
apt install -y --no-install-recommends libgrpc++-dev protobuf-compiler-grpc

# Install Config Rollbacks
apt install -y --no-install-recommends libsqlite3-dev

# Install ZeroMQ
apt install -y --no-install-recommends libzmq5 libzmq3-dev

# Install utilities
apt install -y --no-install-recommends vim
apt install -y --no-install-recommends nload ethtool

# Install snmpd (should run in start.sh)
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

EOF


# ===== ビルドステージ =====
FROM base AS builder

# Based on the official FRR documentation for building on Ubuntu 24.04
# https://docs.frrouting.org/projects/dev-guide/en/latest/building-frr-for-ubuntu2404.html

ENV WORKING_DIRECTORY=/var/tmp/build
ENV DATE=20250905

# WORKDIR ${WORKING_DIRECTORY}

# USER root

RUN <<EOF

mkdir -p ${WORKING_DIRECTORY}
cd ${WORKING_DIRECTORY}

# Install libyang
git clone https://github.com/CESNET/libyang.git
cd libyang
git checkout v2.1.128
mkdir build; cd build
cmake --install-prefix /usr -D CMAKE_BUILD_TYPE:String="Release" ..
make
make install
cd ${WORKING_DIRECTORY}

# Add FRR user and groups
groupadd -r -g 92 frr
groupadd -r -g 85 frrvty
adduser --system --ingroup frr --home /var/run/frr/ --gecos "FRR suite" --shell /sbin/nologin frr
usermod -a -G frrvty frr

# Download FRR source code
export GIT_SSL_NO_VERIFY=true
cd ${WORKING_DIRECTORY}

# stable 10.4
git clone -b stable/10.4 https://github.com/FRRouting/frr.git frr

# latest
# git clone https://github.com/frrouting/frr.git frr

# Compile
# --disable-doc: do not build documentation
# --enable-snmp: build with SNMP support

cd frr
./bootstrap.sh
./configure \
    --includedir=/usr/include \
    --bindir=/usr/bin \
    --sbindir=/usr/lib/frr \
    --libdir=/usr/lib/frr \
    --libexecdir=/usr/lib/frr \
    --sysconfdir=/etc \
    --localstatedir=/var \
    --with-moduledir=/usr/lib/frr/modules \
    --enable-configfile-mask=0640 \
    --enable-logfile-mask=0640 \
    --enable-snmp \
    --enable-multipath=64 \
    --enable-user=frr \
    --enable-group=frr \
    --enable-vty-group=frrvty \
    --with-pkg-git-version \
    --with-pkg-extra-version=${DATE} \
    --disable-doc

make

# Install
make install
install -m 775 -o frr -g frr -d /var/log/frr
install -m 775 -o frr -g frr -d /etc/frr
install -m 640 -o frr -g frr tools/etc/frr/vtysh.conf /etc/frr/vtysh.conf
install -m 640 -o frr -g frr tools/etc/frr/frr.conf /etc/frr/frr.conf
install -m 640 -o frr -g frr tools/etc/frr/daemons.conf /etc/frr/daemons.conf
install -m 640 -o frr -g frr tools/etc/frr/daemons /etc/frr/daemons
install -m 640 -o frr -g frr tools/etc/frr/support_bundle_commands.conf /etc/frr/support_bundle_commands.conf

# enable snmp in /etc/frr/daemons
sed -i '/^zebra_options=/ s/"$/ -M snmp"/' /etc/frr/daemons

#
# snmpd should run in start.sh
# https://raw.githubusercontent.com/takamitsu-iida/expt-cml/refs/heads/master/frr/start.sh
#

# install deadman
cd /root
git clone https://github.com/upa/deadman.git

# Create mountpoint directory
mkdir /config

# Clean up
# apt remove -y
apt autoremove -y
apt clean
cd /
rm -rf /var/lib/apt/lists/*
rm -rf /var/lib/cache/*
rm -rf ${WORKING_DIRECTORY}
unset WORKING_DIRECTORY

EOF

COPY --chmod=0755 start.sh /

ENTRYPOINT ["/start.sh"]
