# Dockerfile for building FRRouting (FRR) on Ubuntu 24.04

ARG UBUNTU_VERSION=24.04
FROM ubuntu:$UBUNTU_VERSION

# Based on the official FRR documentation for building on Ubuntu 24.04
# https://docs.frrouting.org/projects/dev-guide/en/latest/building-frr-for-ubuntu2404.html

ENV TZ Asia/Tokyo
ENV LANG ja_JP.UTF-8
ENV WORKING_DIRECTORY /root

ENV DATE 20250817

WORKDIR $WORKING_DIRECTORY

USER root

RUN apt update \
    && apt upgrade -y \
    && apt install -y \
            git autoconf automake libtool make libreadline-dev texinfo \
            pkg-config libpam0g-dev libjson-c-dev bison flex \
            libc-ares-dev python3-dev python3-sphinx \
            install-info build-essential libsnmp-dev perl \
            libcap-dev libelf-dev libunwind-dev \
            protobuf-c-compiler libprotobuf-c-dev \
    # Install libyang build requirements
    && apt install -y cmake libpcre2-dev \
    # Install libyang
    && git clone https://github.com/CESNET/libyang.git \
    && cd libyang \
    && git checkout v2.1.128 \
    && mkdir build; cd build \
    && cmake --install-prefix /usr -D CMAKE_BUILD_TYPE:String="Release" .. \
    && make \
    && make install \
    && cd ${WORKING_DIRECTORY} \
    # Install GRPC
    && apt install -y libgrpc++-dev protobuf-compiler-grpc \
    # Install Config Rollbacks
    && apt install -y libsqlite3-dev \
    # ZeroMQ
    && apt install -y libzmq5 libzmq3-dev \
    # utilities
    && apt install -y vim \
    # Add FRR user and groups
    && groupadd -r -g 92 frr \
    && groupadd -r -g 85 frrvty \
    && adduser --system --ingroup frr --home /var/run/frr/ --gecos "FRR suite" --shell /sbin/nologin frr \
    && usermod -a -G frrvty frr \
    # Compile
    && export GIT_SSL_NO_VERIFY=true \
    && cd ${WORKING_DIRECTORY} \
    && git clone https://github.com/frrouting/frr.git frr \
    && cd frr \
    && ./bootstrap.sh \
    && ./configure \
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
            --with-pkg-extra-version=-${DATE} \
            --disable-doc \
    && make \
    && make install \
    && install -m 775 -o frr -g frr -d /var/log/frr \
    && install -m 775 -o frr -g frr -d /etc/frr \
    && install -m 640 -o frr -g frr tools/etc/frr/vtysh.conf /etc/frr/vtysh.conf \
    && install -m 640 -o frr -g frr tools/etc/frr/frr.conf /etc/frr/frr.conf \
    && install -m 640 -o frr -g frr tools/etc/frr/daemons.conf /etc/frr/daemons.conf \
    && install -m 640 -o frr -g frr tools/etc/frr/daemons /etc/frr/daemons \
    && install -m 640 -o frr -g frr tools/etc/frr/support_bundle_commands.conf /etc/frr/support_bundle_commands.conf \
    # Clean up
    && apt remove -y \
    && apt clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/lib/cache/* \
    && rm -rf ${WORKING_DIRECTORY}/frr \
    && rm -rf ${WORKING_DIRECTORY}/libyang \
    # Enable IPv4 and IPv6 forwarding
    && sed -i '/^net.ipv6.conf.all.forwarding/s/^.*$/net.ipv6.conf.all.forwarding=1/' /etc/sysctl.conf \
    && grep -q '^net.ipv6.conf.all.forwarding=1' /etc/sysctl.conf || echo 'net.ipv6.conf.all.forwarding=1' >> /etc/sysctl.conf \
    && sed -i '/^net.ipv4.ip_forward/s/^.*$/net.ipv4.ip_forward=1/' /etc/sysctl.conf \
    && grep -q '^net.ipv4.ip_forward=1' /etc/sysctl.conf || echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf

COPY --chmod=0755 start.sh /

CMD ["/start.sh"]
