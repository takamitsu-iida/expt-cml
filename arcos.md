# ArcOS


頂いたファイル

- ファイル名 arcos-sa-1763662203.9bba6c06a052997075193079277be8ce9914c6c3.kvm.qcow2
- サイズ 約2GB

ファイル名からは読み取れないものの、中身は `8.3.1.EFT1:Nov_20_25:6_11_PM` というバージョンです。

これをCMLにSCPで送り込みます。

`scp ./arcos-sa-1763662203.9bba6c06a052997075193079277be8ce9914c6c3.kvm.qcow2 cml:`

実行例。

```bash
iida@s400win:~$ scp ./arcos-sa-1763662203.9bba6c06a052997075193079277be8ce9914c6c3.kvm.qcow2 cml:
Warning: Permanently added '[192.168.122.212]:1122' (ECDSA) to the list of known hosts.
arcos-sa-1763662203.9bba6c06a052997075193079277be8ce9914c6c3.kvm.qcow2                100% 2016MB 362.8MB/s   00:05
```

SSHでCMLに乗り込んで、root特権を取ります。

実行例。

```bash
(.venv) iida@s400win:~/git/expt-cml$ ssh cml
Warning: Permanently added '[192.168.122.212]:1122' (ECDSA) to the list of known hosts.
Welcome to Ubuntu 24.04.2 LTS (GNU/Linux 6.8.0-60-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/pro

This system has been minimized by removing packages and content that are
not required on a system that users do not log into.

To restore this content, you can run the 'unminimize' command.
Web console: https://cml-controller:9090/ or https://255.0.0.0 via 192.168.122.1 dev bridge0 uid 0 \    cache :9090/

Last login: Wed Nov 26 13:40:06 2025 from 192.168.122.198

Version: 2.9.0+build.3
This host is a controller
Compute ID: e1467448-9e7a-4e10-a29a-8a0a10f8681b

iida@cml-controller:~$ sudo -s -E
[sudo] password for iida:
root@cml-controller:~#
```

送ったファイルがあるか確認します。

ホームディレクトリ（この場合は/home/iida）にファイルが転送されています。

実行例。

```bash
root@cml-controller:~# pwd
/home/iida
root@cml-controller:~# ls -l
total 2064772
-rw-r--r-- 1 iida iida 2114322432 Nov 26 13:51 arcos-sa-1763662203.9bba6c06a052997075193079277be8ce9914c6c3.kvm.qcow2
```

イメージ定義を作ります。

CSR1000vのイメージ定義ディレクトリをコピーします。

```bash
root@cml-controller:~# cd /var/lib/libvirt/images/virl-base-images/

root@cml-controller:/var/lib/libvirt/images/virl-base-images# ls
alpine-base-3-21-3            cat-sdwan-validator-20-16-1  firefox-138-0-4-build1        iosvl2-2020         tacplus-f4-0-4-28
alpine-desktop-3-21-3         cat-sdwan-vedge-20-16-1      fmcv-7-7-0                    iosxrv9000-25-1-1   thousandeyes-ea-1-210-0
alpine-trex-3-21-3            cat8000v-17-16-01a           frr-10-2-1-r1                 net-tools-1-0-0     tig
alpine-wanem-3-21-3           cat9000v-q200-17-15-03       frr-10-4                      nginx-3-38          ubuntu-24-04-20250503
arcos                         cat9000v-uadp-17-15-03       ftdv-7-7-0                    nxosv9300-10-5-3-f  ubuntu-24-04-20250503-frr
asav-9-23-1                   cat9800-17-17-01             iol-xe-17-16-01a              radius-3-2-1        ubuntu-24-04-docker
cat-sdwan-controller-20-16-1  chrome-136-0-7103-113-1      iol-xe-17-16-01a-serial-4eth  server-tcl-16-0     ubuntu_docker
cat-sdwan-edge-17-16-01a      csr1000v-17-03-08a           ioll2-xe-17-16-01a            splunk-9-4
cat-sdwan-manager-20-16-1     dnsmasq-2-9-0                iosv-159-3-m10                syslog-3-38

root@cml-controller:/var/lib/libvirt/images/virl-base-images# cp -a csr1000v-17-03-08a arcos
```

arcosのイメージ定義ディレクトリに移動して、イメージ定義ファイルの名前をarcos.yamlに変更する（ディレクトリ名と一致させる）。

```bash
root@cml-controller:/var/lib/libvirt/images/virl-base-images# cd arcos
root@cml-controller:/var/lib/libvirt/images/virl-base-images/arcos# mv csr1000v-17-03-08a.yaml arcos.yaml
```

qcow2ファイルをイメージ定義ディレクトリに移す。オーナーとグループを `libvirt-qemu:virl2` に変更する。

```bash
root@cml-controller:/var/lib/libvirt/images/virl-base-images/arcos# mv ~/arcos-sa-1763662203.9bba6c06a052997075193079277be8ce9914c6c3.kvm.qcow2 .
root@cml-controller:/var/lib/libvirt/images/virl-base-images/arcos# ls -l
total 3452872
-rw-r--r-- 1 iida         iida  2114322432 Nov 26 13:51 arcos-sa-1763662203.9bba6c06a052997075193079277be8ce9914c6c3.kvm.qcow2
-rw-rw-r-- 1 libvirt-qemu virl2        277 Nov 26 13:36 arcos.yaml
-rw-rw-r-- 1 libvirt-qemu virl2 1421410304 Jun 17 12:26 csr1000v-universalk9.17.03.08a-serial.qcow2
root@cml-controller:/var/lib/libvirt/images/virl-base-images/arcos# chown libvirt-qemu:virl2 arcos-sa-1763662203.9bba6c06a052997075193079277be8ce9914c6c3.kvm.qcow2
```

不要なcsr1000vのイメージを削除します。


```bash
root@cml-controller:/var/lib/libvirt/images/virl-base-images/arcos# ls -l
total 3452876
-rw-r--r-- 1 libvirt-qemu virl2 2114322432 Nov 26 13:51 arcos-sa-1763662203.9bba6c06a052997075193079277be8ce9914c6c3.kvm.qcow2
-rw-rw-r-- 1 libvirt-qemu virl2        277 Nov 26 13:36 arcos.yaml
-rw-rw-r-- 1 libvirt-qemu virl2 1421410304 Jun 17 12:26 csr1000v-universalk9.17.03.08a-serial.qcow2

root@cml-controller:/var/lib/libvirt/images/virl-base-images/arcos# rm csr1000v-universalk9.17.03.08a-serial.qcow2
```

イメージ定義ファイルを以下の内容に変更します。

```yaml
#
# arcos image definition
#

id: arcos
label: ArcOS
description: arcos
node_definition_id: arcos
disk_image: arcos-sa-1763662203.9bba6c06a052997075193079277be8ce9914c6c3.kvm.qcow2
read_only: true
schema_version: 0.0.1
```

ノード定義ファイルを作ります。

ノード定義ファイルが置かれている場所に移動します。

```bash
root@cml-controller:/var/lib/libvirt/images/virl-base-images/arcos# cd /var/lib/libvirt/images/node-definitions/
```

CSR1000vのノード定義ファイルをコピーします。

```bash
root@cml-controller:/var/lib/libvirt/images/node-definitions# cp -a csr1000v.yaml arcos.yaml
```

以下の内容に変更します。

```yaml
id: arcos
boot:
  timeout: 120
  completed:
    - Debian GNU/Linux 12 localhost ttyS0
    - ArcOS (c) Arrcus, Inc
  uses_regex: false
sim:
  linux_native:
    libvirt_domain_driver: kvm
    driver: server
    disk_driver: virtio
    ram: 8192
    cpus: 1
    cpu_limit: 100
    nic_driver: vmxnet3
general:
  nature: router
  read_only: false
configuration:
  generator:
    driver: null
device:
  interfaces:
    serial_ports: 2
    physical:
      - ma1
      - swp1
      - swp2
      - swp3
      - swp4
    has_loopback_zero: true
    default_count: 5
    loopback:
      - Loopback
ui:
  label_prefix: arcos-
  icon: router
  label: ArcOS
  visible: true
inherited:
  image:
    ram: true
    cpus: true
    data_volume: true
    boot_disk_size: true
    cpu_limit: true
  node:
    ram: true
    cpus: true
    data_volume: true
    boot_disk_size: true
    cpu_limit: true
schema_version: 0.0.1
```

デフォルトのアカウントでログインします。

- root
- YouReallyNeedToChangeThis

ログインしたらpasswdコマンドでパスワードを変更します。

シェルの起動は `cli` コマンドです。

```text
Welcome to the ArcOS CLI
root connected from 127.0.0.1 using console on R1
root@R1# show version
Platform:         Virtual
Software:         Arrcus ArcOS
Software Version: 8.3.1.EFT1:Nov_20_25:6_11_PM
Firmware MU:
Form Factor:      FF_VIRTUAL
CPU Information:  12th Gen Intel(R) Core(TM) i7-12700, 1 cores
Memory [Total]:   2926092 kB
Uptime:           1 minute
```

設定は `config` コマンドですが、初回起動時はZTPプロセスが走っているため、手動での設定変更はできません。

```text
root@localhost# config
ZTP is in progress. System configuration cannot be changed now. Please stop ZTP using cli "request system ztp stop" to stop ZTP and change system configuration.
```

上記メッセージにある通り `request system ztp stop` で停止します。

設定できるようになりますが・・・

```text
root@localhost# request system ztp stop
Are you sure? This command will disable ZTP and may take several minutes (up to 10 minutes) [no,yes] yes

Initiating ZTP stop. Please do not perform any operation on the system until ZTP is stopped...
2025-11-27 09:00:33 ArcOS ztp INFO: Stopping ZTP...
```

```text
root@localhost# config
Entering configuration mode terminal

root@localhost(config)# interface ?
Possible completions:
  ma1
  swp1
  swp2
  swp3
  swp4
root@localhost(config)# interface swp1
root@localhost(config-interface-swp1)# enabled
root@localhost(config-interface-swp1)# commit
Aborted: 'interface swp1 enabled': Admin user password (system aaa authentication admin-user) still not changed from factory default password. Interfaces cannot be enabled!

root@localhost(config-interface-swp1)#
```

このように、最初にAdminユーザのパスワードを変更しないと、設定の変更は許可してもらえません。

この設定を行います。

```text
root@localhost(config)# system aaa authentication admin-user admin-password
(<hash digest string>): ********
root@localhost(config)#
root@localhost(config)# commit
Commit complete.
root@localhost(config)#
```

設定をテキストファイルに保存します。

```text
root@localhost# show running-config | save run-conf.txt
```

exitでシェルを抜けてbashに戻ると、ファイルを確認できます。中身はこんな感じ。

```bash
root@localhost:~# ls
run-conf.txt
root@localhost:~#
root@localhost:~# cat run-conf.txt
version "8.3.1.EFT1:Nov_20_25:6_11_PM [release] 2025-11-20 18:11:22"
features feature ARCOS_RIOT
 supported false
!
features feature ARCOS_ICMP_SRC_REWRITE
 supported true
!
features feature ARCOS_SUBIF
 supported true
!
features feature ARCOS_QoS
 supported false
!
features feature ARCOS_MPLS
 supported true
!
features feature ARCOS_SFLOW
 supported true
!
system login-banner "ArcOS (c) Arrcus, Inc."
system cli commit-message true
system netconf-server enable false
system netconf-server transport ssh enable false
system restconf-server enable false
system aaa authentication admin-user admin-password $6$DGq6SqagIDmiu3tA$TxSoLLT7XA5F6vg3/D9VuLauylwOFPQon0ZGn/imwaxLb.Y7tJ4ii.RftGsLvpRkLdrptQDaRyT5Ah8D.ihXZ1
system rib IPV6
!
system rib IPV4
!
interface ma1
 type    ethernetCsmacd
 mtu     1500
 enabled true
 subinterface 0
 exit
!
interface swp1
 type    ethernetCsmacd
 enabled true
!
network-instance default
!
network-instance management
 interface ma1
 !
!
lldp interface ma1
!
lldp interface swp1
!
routing-policy defined-sets prefix-set __IPV4_MARTIAN_PREFIX_SET__
 prefix 0.0.0.0/8 8..32
 !
 prefix 127.0.0.0/8 8..32
 !
 prefix 192.0.0.0/24 24..32
 !
 prefix 224.0.0.0/4 exact
 !
 prefix 224.0.0.0/24 exact
 !
 prefix 240.0.0.0/4 4..32
 !
!
routing-policy defined-sets prefix-set __IPV6_MARTIAN_PREFIX_SET__
 prefix ::/128 exact
 !
 prefix ::1/128 exact
 !
 prefix ff00::/8 exact
 !
 prefix ff02::/16 exact
 !
!
root@localhost:~#
```

このように別ファイルに保存することはできるものの、commitしたときにどこに保存されているかは不明です。

## 注意事項

<br>

### MTUに注意

arcosのデフォルトでは、インタフェースのMTUが9000になっているが、CMLで動く仮想マシンは9000バイトは使えない模様。
ISISのhelloはパディングを詰めてMTU長一杯のパケットを送るが、それは受け取れないので隣接が確立できない。
MTUは3000程度に抑えること。

<br>

## cliコマンド

`config` コンフィグモードに遷移します。

`top` コンフィグモードの中で最上位の階層に移動します。

`commit` コンフィグを確定します。

`show configuration` コミット前の編集されている設定を表示します。


`show network-instance default protocol ISIS core interface * state`




<br><br><br>

### SRv6

ロケータ長 64ビット

Cisco IOS-XRの場合、

64 = (SIDブロック 40ビット) + (ノード長 24ビット)

という構成。

ここでは、

64 = (SIDブロック 48ビット) + (ノード長 16ビット)

という形にします。

```text
 srv6 locator MAIN
  locator-node-length 16
  prefix              fd00:0:0:1::/64
 !
```

R1のロケータ fd00:0000:00  00:00:01::/64

```text
 !
 srv6 locator MAIN
  locator-node-length 24
  prefix              fd00:0:0:1::/64
 !
```

R2のロケータ fd00:0000:00  00:00:02::/64

```text
 !
 srv6 locator MAIN
  locator-node-length 24
  prefix              fd00:0:0:2::/64
 !
```


ローカルSID

```text
root@R1# show network-instance default srv6 local-sids
srv6 local-sids local-sid fd00:0:0:1:1::/80
 behavior     END_PSP_USD
 locator-name MAIN
 client-name  sidmgr
```

このローカルSIDをloopback0に割り当てたいけど、subinterface 0に複数のIPv6アドレスを割り当てられない。

かといって、subinterface 1を作ろうとすると怒られる。

これは意味がわからない。loopback 1を作れってことか？？？

<br>

### L3VPN over SRv6

L3VPN_UNICASTをなんとか通せた。

R1の設定

```text
version "8.3.1.EFT1:Nov_20_25:6_11_PM [release] 2025-11-20 18:11:22"
features feature ARCOS_RIOT
 supported false
!
features feature ARCOS_ICMP_SRC_REWRITE
 supported true
!
features feature ARCOS_SUBIF
 supported true
!
features feature ARCOS_QoS
 supported false
!
features feature ARCOS_MPLS
 supported true
!
features feature ARCOS_SFLOW
 supported true
!
system hostname R1
system login-banner "ArcOS (c) Arrcus, Inc."
system clock timezone-name Asia/Tokyo
system ssh-server enable true
system ssh-server permit-root-login true
system cli commit-message true
system netconf-server enable false
system netconf-server transport ssh enable false
system restconf-server enable false
system aaa authentication admin-user admin-password $6$DGq6SqagIDmiu3tA$TxSoLLT7XA5F6vg3/D9VuLauylwOFPQon0ZGn/imwaxLb.Y7tJ4ii.RftGsLvpRkLdrptQDaRyT5Ah8D.ihXZ1
system rib IPV6
!
system rib IPV4
!
interface ma1
 type    ethernetCsmacd
 mtu     1500
 enabled true
 subinterface 0
  ipv4 enabled true
 exit
!
interface swp1
 type    ethernetCsmacd
 mtu     3000
 enabled true
 subinterface 0
  ipv6 enabled true
  ipv4 enabled true
  ipv4 address 192.168.12.1
   prefix-length 24
  exit
  enabled true
 exit
!
interface swp2
 type    ethernetCsmacd
 mtu     3000
 enabled true
 subinterface 10
  ipv6 enabled true
  ipv4 enabled true
  ipv4 address 10.0.1.1
   prefix-length 24
  exit
  enabled true
  vlan vlan-id 10
 exit
!
interface loopback0
 type    softwareLoopback
 mtu     3000
 enabled true
 subinterface 0
  ipv6 enabled true
  ipv6 address 2001:db8:ffff::1
   prefix-length 128
  exit
  ipv4 enabled true
  ipv4 address 192.168.255.1
   prefix-length 32
  exit
  enabled true
 exit
!
network-instance default
 protocol BGP MAIN
  global as 65000
  global router-id 192.168.255.1
  global segment-routing enabled true
  global graceful-restart enabled true
  global afi-safi L3VPN_IPV6_UNICAST
  !
  global afi-safi L3VPN_IPV4_UNICAST
  !
  global srv6 locator MAIN
  neighbor 192.168.255.2
   peer-as 65000
   transport local-address 192.168.255.1
   afi-safi L3VPN_IPV6_UNICAST
    exit
   !
   afi-safi L3VPN_IPV4_UNICAST
    exit
   !
   exit
  !
  neighbor 2001:db8:ffff::2
   peer-as 65000
   transport local-address 2001:db8:ffff::1
   afi-safi L3VPN_IPV6_UNICAST
    exit
   !
   afi-safi L3VPN_IPV4_UNICAST
    exit
   !
   exit
  !
 !
 protocol ISIS MAIN
  global net [ 49.0000.0000.0000.0001.00 ]
  global graceful-restart enabled true
  global segment-routing enabled true
  global traffic-engineering ipv4-router-id 192.168.255.1
  global af IPV6 UNICAST
   enabled true
   exit
  !
  global af IPV4 UNICAST
   enabled true
   exit
  !
  global srv6 enabled true
  global srv6 locator MAIN
  !
  level 1
   enabled true
   exit
  !
  level 2
   enabled false
   exit
  !
  interface swp1
   enabled      true
   network-type POINT_TO_POINT
   af IPV6 UNICAST
    enabled true
   !
   af IPV4 UNICAST
    enabled true
   !
   level 1
    enabled true
    exit
   !
   level 2
    enabled false
    exit
   !
   exit
  !
  interface loopback0
   enabled true
   passive true
   af IPV6 UNICAST
    enabled true
   !
   af IPV4 UNICAST
    enabled true
   !
   level 1
    enabled true
    exit
   !
   level 2
    enabled false
    exit
   !
   exit
  !
 !
 srv6 locator MAIN
  locator-node-length 16
  prefix              fd00:0:0:1::/64
 !
!
network-instance management
 interface ma1
 !
!
network-instance vrf-1
 type L3VRF
 table-connection DIRECTLY_CONNECTED BGP IPV4
 !
 interface swp2.10
 !
 protocol BGP vrf-1
  global segment-routing enabled true
  global route-distinguisher 192.168.255.1:1
  global sid-allocation-mode PER_NEXTHOP
  global afi-safi IPV4_UNICAST
   graceful-restart enabled true
   network 10.0.1.0/24
   !
   rt-afi-safi L3VPN_IPV4_UNICAST
    route-target 65000:1 import
     exit
    !
    route-target 65000:1 export
     exit
    !
    exit
   !
  !
  global afi-safi IPV6_UNICAST
  !
  global srv6 locator MAIN
  neighbor 10.0.1.100
   peer-as 65001
   afi-safi IPV4_UNICAST
    next-hop SELF
    extended-nexthop enable true
    exit
   !
   exit
  !
 !
!
lldp interface ma1
!
lldp interface swp1
!
lldp interface swp2
!
routing-policy defined-sets prefix-set __IPV4_MARTIAN_PREFIX_SET__
 prefix 0.0.0.0/8 8..32
 !
 prefix 127.0.0.0/8 8..32
 !
 prefix 192.0.0.0/24 24..32
 !
 prefix 224.0.0.0/4 exact
 !
 prefix 224.0.0.0/24 exact
 !
 prefix 240.0.0.0/4 4..32
 !
!
routing-policy defined-sets prefix-set __IPV6_MARTIAN_PREFIX_SET__
 prefix ::/128 exact
 !
 prefix ::1/128 exact
 !
 prefix ff00::/8 exact
 !
 prefix ff02::/16 exact
 !
!
```

R2の設定

```text
version "8.3.1.EFT1:Nov_20_25:6_11_PM [release] 2025-11-20 18:11:22"
features feature ARCOS_RIOT
 supported false
!
features feature ARCOS_ICMP_SRC_REWRITE
 supported true
!
features feature ARCOS_SUBIF
 supported true
!
features feature ARCOS_QoS
 supported false
!
features feature ARCOS_MPLS
 supported true
!
features feature ARCOS_SFLOW
 supported true
!
system hostname R2
system login-banner "ArcOS (c) Arrcus, Inc."
system clock timezone-name Asia/Tokyo
system ssh-server enable true
system ssh-server permit-root-login true
system cli commit-message true
system netconf-server enable false
system netconf-server transport ssh enable false
system restconf-server enable false
system aaa authentication admin-user admin-password $6$HAOaiOJfXV4ybYH9$55sa2AWuPptssaV1eo.5WRDi/wBv/TmqFbFMRlccF7twXLko37CGIVP9OOy4qUTKkQTZrNkrt7cwRZ0Tm6Gwn1
system rib IPV6
!
system rib IPV4
!
interface ma1
 type    ethernetCsmacd
 mtu     1500
 enabled true
 subinterface 0
  ipv4 enabled true
  enabled true
 exit
!
interface swp1
 type    ethernetCsmacd
 mtu     3000
 enabled true
 subinterface 0
  ipv6 enabled true
  ipv4 enabled true
  ipv4 address 192.168.12.2
   prefix-length 24
  exit
  enabled true
 exit
!
interface swp2
 type    ethernetCsmacd
 mtu     3000
 enabled true
 subinterface 10
  ipv6 enabled true
  ipv4 enabled true
  ipv4 address 10.0.2.1
   prefix-length 24
  exit
  enabled true
  vlan vlan-id 10
 exit
!
interface loopback0
 type    softwareLoopback
 mtu     3000
 enabled true
 subinterface 0
  ipv6 enabled true
  ipv6 address 2001:db8:ffff::2
   prefix-length 128
  exit
  ipv4 enabled true
  ipv4 address 192.168.255.2
   prefix-length 32
  exit
  enabled true
 exit
!
network-instance default
 protocol BGP MAIN
  global as 65000
  global router-id 192.168.255.2
  global segment-routing enabled true
  global graceful-restart enabled true
  global afi-safi L3VPN_IPV6_UNICAST
  !
  global afi-safi L3VPN_IPV4_UNICAST
  !
  global srv6 locator MAIN
  neighbor 192.168.255.1
   peer-as 65000
   transport local-address 192.168.255.2
   afi-safi L3VPN_IPV6_UNICAST
    exit
   !
   afi-safi L3VPN_IPV4_UNICAST
    exit
   !
   exit
  !
  neighbor 2001:db8:ffff::1
   peer-as 65000
   transport local-address 2001:db8:ffff::2
   afi-safi L3VPN_IPV6_UNICAST
    exit
   !
   afi-safi L3VPN_IPV4_UNICAST
    exit
   !
   exit
  !
 !
 protocol ISIS MAIN
  global net [ 49.0000.0000.0000.0002.00 ]
  global graceful-restart enabled true
  global segment-routing enabled true
  global traffic-engineering ipv4-router-id 192.168.255.2
  global af IPV6 UNICAST
   enabled true
   exit
  !
  global af IPV4 UNICAST
   enabled true
   exit
  !
  global srv6 enabled true
  global srv6 locator MAIN
  !
  level 1
   enabled true
   exit
  !
  level 2
   enabled false
   exit
  !
  interface swp1
   enabled      true
   network-type POINT_TO_POINT
   af IPV6 UNICAST
    enabled true
   !
   af IPV4 UNICAST
    enabled true
   !
   level 1
    enabled true
    exit
   !
   level 2
    enabled false
    exit
   !
   exit
  !
  interface loopback0
   enabled true
   passive true
   af IPV6 UNICAST
    enabled true
   !
   af IPV4 UNICAST
    enabled true
   !
   level 1
    enabled true
    exit
   !
   level 2
    enabled false
    exit
   !
   exit
  !
 !
 srv6 locator MAIN
  locator-node-length 16
  prefix              fd00:0:0:2::/64
 !
!
network-instance management
 interface ma1
 !
!
network-instance vrf-1
 type L3VRF
 table-connection DIRECTLY_CONNECTED BGP IPV4
 !
 interface swp2.10
 !
 protocol BGP vrf-1
  global segment-routing enabled true
  global route-distinguisher 192.168.255.2:1
  global sid-allocation-mode PER_NEXTHOP
  global afi-safi IPV4_UNICAST
   graceful-restart enabled true
   network 10.0.2.0/24
   !
   rt-afi-safi L3VPN_IPV4_UNICAST
    route-target 65000:1 import
     exit
    !
    route-target 65000:1 export
     exit
    !
    exit
   !
  !
  global afi-safi IPV6_UNICAST
  !
  global srv6 locator MAIN
  neighbor 10.0.2.100
   peer-as 65002
   afi-safi IPV4_UNICAST
    next-hop SELF
    exit
   !
   exit
  !
 !
!
lldp interface ma1
!
lldp interface swp1
!
lldp interface swp2
!
routing-policy defined-sets prefix-set __IPV4_MARTIAN_PREFIX_SET__
 prefix 0.0.0.0/8 8..32
 !
 prefix 127.0.0.0/8 8..32
 !
 prefix 192.0.0.0/24 24..32
 !
 prefix 224.0.0.0/4 exact
 !
 prefix 224.0.0.0/24 exact
 !
 prefix 240.0.0.0/4 4..32
 !
!
routing-policy defined-sets prefix-set __IPV6_MARTIAN_PREFIX_SET__
 prefix ::/128 exact
 !
 prefix ::1/128 exact
 !
 prefix ff00::/8 exact
 !
 prefix ff02::/16 exact
 !
!
```
