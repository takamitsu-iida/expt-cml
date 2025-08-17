# Dockerfile for building FRRouting (FRR) on Ubuntu 24.04

ARG UBUNTU_VERSION=24.04
FROM ubuntu:$UBUNTU_VERSION

# Based on the official FRR documentation for building on Ubuntu 24.04
# https://docs.frrouting.org/projects/dev-guide/en/latest/building-frr-for-ubuntu2404.html

USER root
WORKDIR /root

COPY start.sh /start.sh

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
    # Install GRPC
    && apt install -y libgrpc++-dev protobuf-compiler-grpc \
    # Install Config Rollbacks
    && apt install -y libsqlite3-dev \
    # ZeroMQ
    && apt install -y libzmq5 libzmq3-dev \
    #
    # Utilities
    #
    && apt install -y \
            vim \
            iputils-ping \
            tcpdump \
    && rm -rf /var/lib/apt/lists/* \
    && mv /bin/ping /sbin/ping \
    && mv /bin/ping6 /sbin/ping6 \
    && mv /usr/sbin/tcpdump /usr/bin/tcpdump \
    ###########################
    # Building & Installing FRR
    ###########################
    # Add FRR user and groups
    && groupadd -r -g 92 frr \
    && groupadd -r -g 85 frrvty \
    && adduser --system --ingroup frr --home /var/run/frr/ --gecos "FRR suite" --shell /sbin/nologin frr \
    && usermod -a -G frrvty frr \
    # Compile
    && export GIT_SSL_NO_VERIFY=true \
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
            --enable-gcov \
            --enable-rpki \
            --enable-sharpd \
            --enable-multipath=256 \
            --enable-config-rollbacks \
            --enable-grpc \
            --enable-protobuf \
            --enable-scripting \
            --with-pkg-git-version \
            --with-pkg-extra-version=-MyOwnFRRVersion
    && make \
    && make install \



COPY --chmod=0755 start.sh /

CMD ["/start.sh"]
