#!/bin/bash

cd /var/lib/libvirt/images/virl-base-images

mkdir frr-10-5-iida

cd frr-10-5-iida

if [ /var/local/virl2/dropfolder/frr.tar.gz ]; then
    mv /var/local/virl2/dropfolder/frr.tar.gz .
else
    echo "frr.tar.gz not exists, skipping."
fi


cat << 'EOF' > frr-10-5-iida.yaml
#
# Free Range Routing node definition
# generated 2025-08-15
# part of VIRL^2
#

id: frr-10-5-iida
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
              "image": "ubuntu24:frr10.5",
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
          !
          hostname frr-0
          !
          interface lo
              !no ip address
          !
          interface eth0
              !no ip address
              no shutdown
          interface eth1
              !no ip address
              shutdown
          interface eth2
              !no ip address
              shutdown
          interface eth3
              !no ip address
              shutdown
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
          bgpd
          # ospfd
          # ospf6d
          # ripd
          # ripngd
          # isisd
          # pimd
          # pim6d
          # ldpd
          # nhrpd
          # eigrpd
          # babeld
          # sharpd
          # pbrd
          # bfdd
          fabricd
          # vrrpd
          # pathd
device:
  interfaces:
    has_loopback_zero: false
    min_count: 1
    default_count: 8
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
    Free Range Routing (frr) 10.5
  group: Others
  icon: router
  label: FRR
  label_prefix: frr-
  visible: true

EOF
