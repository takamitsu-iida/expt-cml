# FRR(Docker)でOpenFabricを検証する

CML2.9以降でDockerイメージが動作するようになっています。

2025年8月時点、FRRのDocker版のバージョンは `FRRouting 10.2.1` です。

このバージョンではOpenFabricはうまく動かないようです。

<br>

## ラボ構成

スクリプト `bin/cml_create_openfabric_docker_lab.py` を使ってCML内にラボを自動生成します。

<br>

![ラボ構成](/assets/openfabric_docker_lab.png)

<br>

## なんかおかしい

設定をみたときに　`no ipv6 forwarding`　となっていて、IPv6の中継ができなくなっています。

```text
R1# show run
Building configuration...

Current configuration:
!
frr version 10.2.1
frr defaults traditional
hostname R1
log syslog informational
no ipv6 forwarding
service integrated-vtysh-config
!
```

IPv6のリンクローカルアドレスを固定で設定しているのに、自動で割り当ててしまっています。

```text
R1# show int brief
Interface       Status  VRF             Addresses
---------       ------  ---             ---------
eth0            up      default         + fe80::5054:ff:fec9:be76/64
eth1            up      default         + fe80::1/64
eth2            up      default         + fe80::1/64
eth3            up      default         + fe80::5054:ff:fe73:ed68/64
eth4            up      default         fe80::1/64
eth5            up      default         fe80::1/64
eth6            up      default         fe80::1/64
eth7            up      default         fe80::1/64
lo              up      default         192.168.255.1/32
                                        2001:db8::1/128
```

<br><br><br>

# FRRのDockerイメージを作る

FRRの公式マニュアルにDockerイメージの作り方が書かれていますので、それに従います。

https://docs.frrouting.org/projects/dev-guide/en/latest/building-docker.html

<br>

## （事前準備）FRRをコンパイルする

そもそもコンパイルが通らなければDockerのイメージを作りようがありません。

環境を整える意味でも、一度コンパイルします。

FRRのコンパイル方法は　[こちら](/README.create_frr_image.md)　にあります。

<br>

## Dockerをインストールする

FRRを問題なくコンパイルできることを確認したら、Dockerイメージにします。

Dockerのインストールが必要ですので、事前準備として必要なツールをインストールします。

```bash
sudo apt update
sudo apt install ca-certificates curl gnupg
```

aptリポジトリを追加します。

```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
```

dockerグループを作成してciscoアカウントをグループに所属させます（デフォルトのアカウントがciscoの場合）。

```bash
sudo groupadd docker
sudo usermod -aG docker cisco
```

docker-engineをインストールします。

```bash
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

再起動します。

```bash
sudo reboot
```

<br>

> [!NOTE]
>
> dockerコマンド早見表
>
> `docker ps -a`　止まっているものを含めてプロセスを確認
> `docker stop`　停止
> `docker rm`　削除
> `docker image ls`　存在するイメージの確認
> `docker rmi`　イメージを削除
> `docker system prune --all`　キャッシュの削除、再ビルドする前に実行
> `docker tag IMAGE_ID IMAGE_NAME:TAG`　作成済みイメージの名前とタグを変更
> `docker exec -it ID bash`　シェルを起動

<br>

## Dockerイメージをビルドします

<br>

> [!NOTE]
>
> FRRのDockerイメージは Alpine か Centos でビルドできます。UbuntuはTravis CI用です。

<br>

FRRのソースコードの場所に移動します。

```bash
cd frr
```

Alpineイメージを作ります。

```bash
docker build -f docker/alpine/Dockerfile -t frr-alpine:latest .
```

<br>

> [!NOTE]
>
> 再ビルドの場合、古いキャッシュが悪さをするかもしれないので、念の為削除してから実行します。
>
> `docker system prune --all`

<br>

イメージを確認します。

```bash
docker image ls
```

実行例。

```bash
cisco@inserthostname-here:~/frr$ docker image ls
REPOSITORY   TAG       IMAGE ID       CREATED         SIZE
frr-alpine   latest    a284f9e91053   2 minutes ago   194MB
```

```bash
cisco@inserthostname-here:~/frr$ docker image ls
REPOSITORY   TAG                 IMAGE ID       CREATED             SIZE
frr          alpine-3f0815f4e0   69791b5d3028   About an hour ago   194MB
```

タグが気に入らないので直します。

```bash
docker tag 69791b5d3028 frr:latest
```



動かしてみます。

```bash
docker run -d --init --privileged --name frr frr:latest
```

接続します。

```bash
docker exec -it frr bash
```

/usr/lib/frr/frrinit.sh start


vtyshに入ります。

```bash
sudo -s -E
vtysh
```

なんかおかしい・・・

設定が保存されない。


停止します。

```bash
docker stop frr
```

コンテナを削除します。

```bash
docker rm frr
```

イメージをtar形式でセーブします。

```bash
docker save frr-alpine:latest > frr.tar
```

圧縮します。

```bash
gzip frr.tar
```

アップロードします。

```bash
scp frr.tar.gz admin@192.168.122.212:
```

コックピット側のdropfolderから移動します。

```bash
mv /var/local/virl2/dropfolder/frr.tar.gz /home/admin/
```

イメージ定義ファイルをコピーします。

```bash
cp /var/lib/libvirt/images/virl-base-images/frr-10-2-1-r1/frr-10-2-1-r1.yaml .
```

SHA256を計算します。

```bash
sha256sum frr.tar.gz
```

実行例

```bash
root@cml-controller:~# sha256sum frr.tar.gz
71e2b8fcbf3e2570b2bec387b5b31456aff901cfcc997f1ce2b1dbbef2313afd  frr.tar.gz
```



<br>

# いろいろ調査してみる

CMLで適当なラボを作って、FRRイメージをインスタンス化して起動してみる。

コックピットのターミナルで確認すると、イメージの置かれているディレクトリにいくつかファイルがある。

`boot.sh`　と　`node.cfg`　と　`protocols`　はCMLのウェブ画面で指定する設定ファイル。

```bash
root@cml-controller:/var/local/virl2/images/5ae0eb2d-ec7f-4ef4-a610-1a22f854cd11/894b8a48-3a9f-46d9-bf9f-c3d649dac49c/cfg# ls -l
total 16
-rw-r--r-- 1 virl2 virl2  99 Aug 15 06:44 boot.sh
-rw-r--r-- 1 virl2 virl2 734 Aug 15 06:44 config.json
-rw-r--r-- 1 virl2 virl2 665 Aug 15 06:44 node.cfg
-rw-r--r-- 1 virl2 virl2 249 Aug 15 06:44 protocols
```

`config.json`　はdockerの設定ファイル。

中身はこんな感じ。

```bash
root@cml-controller:/var/local/virl2/images/5ae0eb2d-ec7f-4ef4-a610-1a22f854cd11/894b8a48-3a9f-46d9-bf9f-c3d649dac49c/cfg# cat config.json
{
  "docker": {
    "image": "frr:10.2.1-r1",
    "mounts": [
      "type=bind,source=cfg/boot.sh,target=/config/boot.sh",
      "type=bind,source=cfg/node.cfg,target=/config/node.cfg",
      "type=bind,source=cfg/protocols,target=/config/protocols"
    ],
    "caps": [
      "CAP_CHOWN",
      "CAP_DAC_OVERRIDE",
      "CAP_FOWNER",
      "CAP_FSETID",
      "CAP_KILL",
      "CAP_MKNOD",
      "CAP_NET_BIND_SERVICE",
      "CAP_NET_RAW",
      "CAP_SETFCAP",
      "CAP_SETGID",
      "CAP_SETPCAP",
      "CAP_SETUID",
      "CAP_SYS_CHROOT",
      "NET_ADMIN",
      "SYS_ADMIN"
    ],
    "env": [
      "MAX_FDS=100000"
    ]
  },
  "shell": "/bin/bash",
  "day0cmd": [ "/bin/bash", "/config/boot.sh" ],
  "busybox": true
}
```

インスタンス化するたびにこれらファイルが作られるということは、
どこかでこれらファイルを作成するように指示してはずなんだけど、どこだろう？

ノード定義ファイルを覗いてみる。

```bash
root@cml-controller:/var/lib/libvirt/images/node-definitions# cat frr.yaml
#
# Free Range Routing node definition
# generated 2025-05-27
# part of VIRL^2
#

id: frr
configuration:
  generator:
    driver: iosv
  provisioning:
    volume_name: cfg
    media_type: raw
    files:
      - name: config.json
        editable: false
        content: |
          {
            "docker": {
              "image": "frr:10.2.1-r1",
              "mounts": [
                "type=bind,source=cfg/boot.sh,target=/config/boot.sh",
                "type=bind,source=cfg/node.cfg,target=/config/node.cfg",
                "type=bind,source=cfg/protocols,target=/config/protocols"
              ],
              "caps": [
                "CAP_CHOWN",
                "CAP_DAC_OVERRIDE",
                "CAP_FOWNER",
                "CAP_FSETID",
                "CAP_KILL",
                "CAP_MKNOD",
                "CAP_NET_BIND_SERVICE",
                "CAP_NET_RAW",
                "CAP_SETFCAP",
                "CAP_SETGID",
                "CAP_SETPCAP",
                "CAP_SETUID",
                "CAP_SYS_CHROOT",
                "NET_ADMIN",
                "SYS_ADMIN"
              ],
              "env": [
                "MAX_FDS=100000"
              ]
            },
            "shell": "/bin/bash",
            "day0cmd": [ "/bin/bash", "/config/boot.sh" ],
            "busybox": true
          }
      - name: node.cfg
        editable: true
        content: |
          ! FRR Config generated on 2025-01-22 17:55
          ! just an example -- You need to need to change it
          !
          hostname frr-0
          !
          interface lo
              ip address 10.0.0.1/32
              ip ospf passive
          !
          interface eth0
              description to eth0.frr-1
              ip address 172.16.128.2/30
              no shutdown
          interface eth1
              description to eth0.frr-2
              ip address 172.16.128.9/30
              no shutdown
          interface eth2
              description not connected
              !no ip address
              shutdown
          interface eth3
              description not connected
              !no ip address
              shutdown
          !
          router ospf
              ospf router-id 10.0.0.1
              network 10.0.0.1/32 area 10
              network 172.16.128.0/30 area 10
              network 172.16.128.8/30 area 10
          !
          end
      - name: boot.sh
        editable: true
        content: |
          # insert more commands here
          # ip address add dev eth1 10.0.0.1/24
          # ip link set dev eth1 up
          exit 0
      - name: protocols
        editable: true
        content: |
          # enable / disable needed routing protocols by adding / removing
          # the hashmark in front of the lines below
          #
          # bgpd
          ospfd
          # ospf6d
          # ripd
          ripngd
          # isisd
          # pimd
          # pim6d
          # ldpd
          # nhrpd
          eigrpd
          # babeld
          # sharpd
          # pbrd
          # bfdd
          # fabricd
          # vrrpd
          # pathd
device:
  interfaces:
    has_loopback_zero: false
    min_count: 1
    default_count: 4
    management:
      - eth0
    physical:
      - eth0
      - eth1
      - eth2
      - eth3
      - eth4
      - eth5
      - eth6
      - eth7
      - eth8
      - eth9
      - eth10
      - eth11
      - eth12
      - eth13
      - eth14
      - eth15
      - eth16
      - eth17
      - eth18
      - eth19
      - eth20
      - eth21
      - eth22
      - eth23
      - eth24
      - eth25
      - eth26
      - eth27
      - eth28
      - eth29
      - eth30
      - eth31
    serial_ports: 2
inherited:
  image:
    ram: true
    cpus: true
    cpu_limit: true
    data_volume: false
    boot_disk_size: false
  node:
    ram: true
    cpus: true
    cpu_limit: true
    data_volume: false
    boot_disk_size: false
general:
  description: Free Range Routing (Docker)
  nature: router
  read_only: true
schema_version: 0.0.1
sim:
  linux_native:
    cpus: 1
    ram: 256
    driver: server
    libvirt_domain_driver: docker
    cpu_limit: 100
boot:
  timeout: 30
  completed:
    - READY
pyats:
  os: ios
  series: iosv
  config_extract_command: show run
ui:
  description: |
    Free Range Routing (frr) 10.2.1-r1
  group: Others
  icon: router
  label: FRR
  label_prefix: frr-
  visible: true
```

なるほど、疑問解消。

ノード定義ファイルにしたがってイメージをインスタンス化するときに `files:` で指定したファイルが生成されるわけだ。

そのうちの一つが `config.json` で、Dockerに対する指示はここに書かれている。

```YAML
    files:
      - name: config.json
        editable: false
        content: |
          {
            "docker": {
              "image": "frr:10.2.1-r1",
              "mounts": [
                "type=bind,source=cfg/boot.sh,target=/config/boot.sh",
                "type=bind,source=cfg/node.cfg,target=/config/node.cfg",
                "type=bind,source=cfg/protocols,target=/config/protocols"
              ],

```

上記のように config.json では起動するイメージを指定しているので、
同じノード定義ファイルでイメージ定義だけ差し替える、ということはできないことになる。

結論としては、ノード定義とイメージ定義の両方を作らないといけないってことかな。

<br>

今度は起動しているFRRイメージにシェルで接続してみる。

```bash
root@cml-controller:~# docker ps
CONTAINER ID   IMAGE           COMMAND       CREATED         STATUS         PORTS     NAMES
5038c95009ce   frr:10.2.1-r1   "/start.sh"   3 minutes ago   Up 3 minutes             894b8a48-3a9f-46d9-bf9f-c3d649dac49c

root@cml-controller:~# docker exec -it 5038c95009ce bash

frr-0:/# cat /etc/os-release
NAME="Alpine Linux"
ID=alpine
VERSION_ID=3.21.3
PRETTY_NAME="Alpine Linux v3.21"
HOME_URL="https://alpinelinux.org/"
BUG_REPORT_URL="https://gitlab.alpinelinux.org/alpine/aports/-/issues"
```

このイメージはAlpineをベースにして動作していることがわかる。だからIPv6あたりの挙動がおかしいのかも。

/start.shが実行されているので、その中身を確認してみる。

このファイルはコンテナの中に焼かれているので、ビルド時にコピーして渡しているはず。

```bash
frr-0:/# cat start.sh
#!/bin/bash

CONFIG=/config/node.cfg
BOOT=/config/boot.sh
PROTOCOLS=/config/protocols

# Not needed for Docker
# for iface in /sys/class/net/*; do
#   iface_name=$(basename "$iface")
#   if /usr/sbin/ethtool "$iface_name" &>/dev/null; then
#     /usr/sbin/ethtool -K "$iface_name" tx off
#   fi
# done

# enable the requested protocols
while IFS= read -r line; do
    line=$(echo "$line" | xargs) # no whitespace
    if [[ -n "$line" && ! "$line" =~ ^# ]]; then
        sed -r -e "s/^(${line}=)no$/\1yes/" -i /etc/frr/daemons
    fi
done <"$PROTOCOLS"

# day0 config for the router
if [ -f $CONFIG ]; then
    cp $CONFIG /etc/frr/frr.conf
fi

# set the hostname from the provided config if it's there
hostname_value="router"
if grep -q "^hostname" $CONFIG; then
    hostname_value=$(awk '/^hostname/ {print $2}' $CONFIG)
fi
hostname $hostname_value

/usr/lib/frr/frrinit.sh start

echo "READY" >/dev/console

trap '' INT TSTP
while true; do
    /usr/bin/vtysh
done
```

/configには確かにファイルが３個ある。

```bash
frr-0:/# ls /config
boot.sh    node.cfg   protocols
frr-0:/#
```

これらファイルはdocker起動時にマウントされて渡されたもので、
イメージをインスタンス化したときに作られるディレクトリ、
すなわちCML本体の `/var/local/virl2/images/ラボのUUID/イメージのUUID/cfg` に実物が置かれている。


以上のことから、UbuntuベースでコンテナをビルドするDockerfileを作ればよさそう。

FRRに同梱のDockerファイルはこんなかんじ。


```text
# Update and install build requirements.
RUN apt update && apt upgrade -y && \
    # Basic build requirements from documentation
    apt-get install -y \
            autoconf \
            automake \
            bison \
            build-essential \
            flex \
            git \
            install-info \
            libc-ares-dev \
            libcap-dev \
            libelf-dev \
            libjson-c-dev \
            libpam0g-dev \
            libreadline-dev \
            libsnmp-dev \
            libsqlite3-dev \
            lsb-release \
            libtool \
            lcov \
            make \
            perl \
            pkg-config \
            python3-dev \
            python3-sphinx \
            screen \
            texinfo \
            tmux \
            iptables \
    && \
    # Protobuf build requirements
    apt-get install -y \
        libprotobuf-c-dev \
        protobuf-c-compiler \
    && \
    # Libyang2 extra build requirements
    apt-get install -y \
        cmake \
        libpcre2-dev \
    && \
    # GRPC extra build requirements
    apt-get install -y \
        libgrpc-dev \
        libgrpc++-dev \
        protobuf-compiler-grpc \
    && \
    # Runtime/triage/testing requirements
    apt-get install -y \
        curl \
        gdb \
        kmod \
        iproute2 \
        iputils-ping \
        liblua5.3-dev \
        libssl-dev \
        lua5.3 \
        net-tools \
        python3 \
        python3-pip \
        snmp \
        snmp-mibs-downloader \
        snmpd \
        ssmping \
        sudo \
        time \
        tshark \
        valgrind \
        yodl \
      && \
    download-mibs && \
    wget --tries=5 --waitretry=10 --retry-connrefused https://raw.githubusercontent.com/FRRouting/frr-mibs/main/iana/IANA-IPPM-METRICS-REGISTRY-MIB -O /usr/share/snmp/mibs/iana/IANA-IPPM-METRICS-REGISTRY-MIB && \
    wget --tries=5 --waitretry=10 --retry-connrefused https://raw.githubusercontent.com/FRRouting/frr-mibs/main/ietf/SNMPv2-PDU -O /usr/share/snmp/mibs/ietf/SNMPv2-PDU && \
    wget --tries=5 --waitretry=10 --retry-connrefused https://raw.githubusercontent.com/FRRouting/frr-mibs/main/ietf/IPATM-IPMC-MIB -O /usr/share/snmp/mibs/ietf/IPATM-IPMC-MIB && \
    rm -f /usr/lib/python3.*/EXTERNALLY-MANAGED && \
    python3 -m pip install wheel && \
    bash -c "PV=($(pkg-config --modversion protobuf | tr '.' ' ')); if (( PV[0] == 3 && PV[1] < 19 )); then python3 -m pip install 'protobuf<4' grpcio grpcio-tools; else python3 -m pip install 'protobuf>=4' grpcio grpcio-tools; fi" && \
    python3 -m pip install 'pytest>=6.2.4' 'pytest-xdist>=3.6.1' 'pytest-asyncio>=0.25.3' && \
    python3 -m pip install 'scapy>=2.4.5' && \
    python3 -m pip install pyyaml && \
    python3 -m pip install xmltodict && \
    python3 -m pip install git+https://github.com/Exa-Networks/exabgp@0659057837cd6c6351579e9f0fa47e9fb7de7311

ARG UID=1010
RUN groupadd -r -g 92 frr && \
      groupadd -r -g 85 frrvty && \
      adduser --system --ingroup frr --home /home/frr \
              --gecos "FRR suite" -u $UID --shell /bin/bash frr && \
      usermod -a -G frrvty frr && \
      useradd -d /var/run/exabgp/ -s /bin/false exabgp && \
      echo 'frr ALL = NOPASSWD: ALL' | tee /etc/sudoers.d/frr && \
      mkdir -p /home/frr && chown frr.frr /home/frr

# Install FRR built packages
RUN mkdir -p /etc/apt/keyrings && \
    curl -s -o /etc/apt/keyrings/frrouting.gpg https://deb.frrouting.org/frr/keys.gpg && \
    echo deb '[signed-by=/etc/apt/keyrings/frrouting.gpg]' https://deb.frrouting.org/frr \
        $(lsb_release -s -c) "frr-stable" > /etc/apt/sources.list.d/frr.list && \
    apt-get update && apt-get install -y librtr-dev libyang2-dev libyang2-tools

USER frr:frr

COPY --chown=frr:frr . /home/frr/frr/

RUN cd ~/frr && \
    ./bootstrap.sh && \
    ./configure \
       --prefix=/usr \
       --sysconfdir=/etc \
       --localstatedir=/var \
       --sbindir=/usr/lib/frr \
       --enable-gcov \
       --enable-dev-build \
       --enable-mgmtd-test-be-client \
       --enable-rpki \
       --enable-sharpd \
       --enable-multipath=256 \
       --enable-user=frr \
       --enable-group=frr \
       --enable-config-rollbacks \
       --enable-grpc \
       --enable-protobuf \
       --enable-vty-group=frrvty \
       --enable-snmp \
       --enable-scripting \
       --with-pkg-extra-version=-my-manual-build && \
    make -j $(nproc) && \
    sudo make install

RUN cd ~/frr && make check || true

COPY docker/ubuntu-ci/docker-start /usr/sbin/docker-start
CMD ["/usr/sbin/docker-start"]

```