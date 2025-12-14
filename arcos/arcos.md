# ArcOS

<br>

## CMLでArcOSを動かす手順

Arrcus社のホームページからリクエストを送って評価版のArcOSのイメージを頂きました。

頂いたファイル

- ファイル名 arcos-sa-1763662203.9bba6c06a052997075193079277be8ce9914c6c3.kvm.qcow2
- サイズ 約2GB

ファイル名からは読み取れないものの、中身は `8.3.1.EFT1:Nov_20_25:6_11_PM` というバージョンです。

このファイルをCML(ホスト名cml)にSCPで送り込みます。

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

scpで送ったファイルを確認します。

ホームディレクトリ（この場合は/home/iida）にファイルが転送されています。

実行例。

```bash
root@cml-controller:~# pwd
/home/iida
root@cml-controller:~# ls -l
total 2064772
-rw-r--r-- 1 iida iida 2114322432 Nov 26 13:51 arcos-sa-1763662203.9bba6c06a052997075193079277be8ce9914c6c3.kvm.qcow2
```

<br>

### イメージ定義

イメージ定義はひとつのファイルではなく、ディレクトリです。

CSR1000vのイメージ定義ディレクトリを属性付きでコピーします。コピー元はCSR1000vでなくても何でもいいです。

実行例。

```bash
root@cml-controller:~# cd /var/lib/libvirt/images/virl-base-images/

root@cml-controller:/var/lib/libvirt/images/virl-base-images# cp -a csr1000v-17-03-08a arcos
```

<br>

コピーしたarcosのイメージ定義ディレクトリに移動して、イメージ定義ファイルの名前をarcos.yamlに変更します（ディレクトリ名と一致させます）。

実行例。

```bash
root@cml-controller:/var/lib/libvirt/images/virl-base-images# cd arcos
root@cml-controller:/var/lib/libvirt/images/virl-base-images/arcos# mv csr1000v-17-03-08a.yaml arcos.yaml
```

<br>

あらかじめ送信したqcow2ファイルをイメージ定義ディレクトリに移して、ファイルのオーナーとグループを `libvirt-qemu:virl2` に変更します。

実行例。

```bash
root@cml-controller:/var/lib/libvirt/images/virl-base-images/arcos# mv ~/arcos-sa-1763662203.9bba6c06a052997075193079277be8ce9914c6c3.kvm.qcow2 .

root@cml-controller:/var/lib/libvirt/images/virl-base-images/arcos# ls -l
total 3452872
-rw-r--r-- 1 iida         iida  2114322432 Nov 26 13:51 arcos-sa-1763662203.9bba6c06a052997075193079277be8ce9914c6c3.kvm.qcow2
-rw-rw-r-- 1 libvirt-qemu virl2        277 Nov 26 13:36 arcos.yaml
-rw-rw-r-- 1 libvirt-qemu virl2 1421410304 Jun 17 12:26 csr1000v-universalk9.17.03.08a-serial.qcow2

root@cml-controller:/var/lib/libvirt/images/virl-base-images/arcos# chown libvirt-qemu:virl2 arcos-sa-1763662203.9bba6c06a052997075193079277be8ce9914c6c3.kvm.qcow2
```

<br>

不要なcsr1000vのイメージを削除します。

実行例。

```bash
root@cml-controller:/var/lib/libvirt/images/virl-base-images/arcos# ls -l
total 3452876
-rw-r--r-- 1 libvirt-qemu virl2 2114322432 Nov 26 13:51 arcos-sa-1763662203.9bba6c06a052997075193079277be8ce9914c6c3.kvm.qcow2
-rw-rw-r-- 1 libvirt-qemu virl2        277 Nov 26 13:36 arcos.yaml
-rw-rw-r-- 1 libvirt-qemu virl2 1421410304 Jun 17 12:26 csr1000v-universalk9.17.03.08a-serial.qcow2

root@cml-controller:/var/lib/libvirt/images/virl-base-images/arcos# rm csr1000v-universalk9.17.03.08a-serial.qcow2
```

<br>

イメージ定義ファイルarcos.yamlを以下の内容に変更します。

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

<br>

### ノード定義ファイル

ノード定義はひとつのファイルです。

ノード定義ファイルが置かれている場所に移動します。

実行例。

```bash
root@cml-controller:/var/lib/libvirt/images/virl-base-images/arcos# cd /var/lib/libvirt/images/node-definitions/
```

<br>

CSR1000vのノード定義ファイルを属性付きでコピーします。コピー元はCSR1000vでなくても構いません。

実行例。

```bash
root@cml-controller:/var/lib/libvirt/images/node-definitions# cp -a csr1000v.yaml arcos.yaml
```

<br>

以下の内容に変更します。

メモリはたくさん割り当てるに越したことはないですが、同時に動かすノードの数を稼ぎたいので控えめに5GB程度にしておきます。

CPUも4CPUくらいあったほうがいいのかもしれませんが、とりあえず1CPUでも動きます。

物理インタフェースは管理インタフェースを含めて合計9個作ります。

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
    ram: 5120
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
      - swp5
      - swp6
      - swp7
      - swp8
    has_loopback_zero: true
    default_count: 9
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

readonlyは**false**を指定します。

<br>

> [!NOTE]
>
> CSR1000vや他の仮想マシンではスタートアップコンフィグを外部から指定できるのですが、ArcOSの場合はやり方が分かりません。
>
> ArcOSは初期状態でZTPが有効なので、それを使うのがいいのかもしれません。

<br>

<br><br>

## 起動後の動作

CMLのダッシュボードでarcosをドラッグドロップでインスタンス化します。

コンソールを開いて、デフォルトのアカウントでログインします。

- root
- YouReallyNeedToChangeThis

ログインしたらpasswdコマンドでパスワードを変更します。

ArcOSのシェルの起動は `cli` コマンドです。

```text
Welcome to the ArcOS CLI
root connected from 127.0.0.1 using console on R1
root@R1
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

<br>

`config` コマンドで設定変更モードに入りますが、初回起動時はZTPプロセスが走っているため、手動での設定変更はできません。

```text
root@localhost# config
ZTP is in progress.
System configuration cannot be changed now.
Please stop ZTP using cli "request system ztp stop" to stop ZTP and change system configuration.
```

上記メッセージにある通り `request system ztp stop` で停止します。

```text
root@localhost# request system ztp stop
Are you sure? This command will disable ZTP and may take several minutes (up to 10 minutes) [no,yes] yes

Initiating ZTP stop. Please do not perform any operation on the system until ZTP is stopped...
2025-11-27 09:00:33 ArcOS ztp INFO: Stopping ZTP...
```

これでコンフィグモードに入れるようになりますが、設定の変更はまだできません。

正確には `commit` ができません。

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
Aborted: 'interface swp1 enabled': Admin user password (system aaa authentication admin-user)
still not changed from factory default password. Interfaces cannot be enabled!

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

これで設定変更できるようになりました。

<br><br>

## 設定をファイルとして保存

設定をテキストファイルに保存します。

```text
root@localhost# show running-config | save run-conf.txt
```

exitでシェルを抜けてbashに戻ると、ファイルを確認できます。中身はこんな感じです。

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

このように別ファイルに保存することはできるものの、commitしたときのコンフィグがどこに保存されているかは不明です。

<br><br>

## 注意事項

<br>

### MTUに注意

ArcOSのデフォルトでは、インタフェースのMTUが9000バイトになっていますが、CMLで動く仮想マシンはそんなに大きなパケットは受け取れないようです。

ISISのhelloはパディングを詰めてMTU長一杯のパケットを送ってきますが、それを受け取れないのでデフォルトのままでは隣接が確立できません。

MTU長は3000程度に抑えるのが良さそうです。

<br><br>

## ip unnumberedでルーティングできない

IPV4であればip unnumberedを設定できます。

隣接ルータとの疎通も問題ありません。

ISISを使えばribも作れるのですが、
Linuxのルーティングテーブルに反映されないので**通信できません**。

こんな感じでribにエントリができていても、

```text
root@PE12# show network-instance default rib IPV4 ipv4-entries entry 10.0.255.11/32
ipv4-entries entry 10.0.255.11/32
 best-protocol ISIS
 hw-update install-ack false
 hw-update status-code 0
 hw-update version 0
 origin ISIS isis-default@MAIN
  metric       20
  pref         115
  label-pref   114
  tag          0
  route-type   ISIS_L1
  nhid         8
  last-updated 2025-12-12T19:23:42.80796-00:00
  flags        ""
  opaque-data  0
  next-hop
   pathid           5
   type             IPV4
   next-hop         10.0.255.2
   network-instance default
   interface        swp2
   weight           100
   flags            ATTACH
  next-hop
   pathid           7
   type             IPV4
   next-hop         10.0.255.1
   network-instance default
   interface        swp1
   weight           100
   flags            ATTACH
```

実際にはLinuxに経路が渡っていないので通信できません。

```text
root@PE12# ping 10.0.255.11
RTNETLINK answers: Network is unreachable
PING 10.0.255.11 (10.0.255.11) from 10.0.255.12 swp1: 56(84) bytes of data.
^C
--- 10.0.255.11 ping statistics ---
2 packets transmitted, 0 received, 100% packet loss, time 1017ms
```

<br><br>

## cliコマンド

`config` コンフィグモードに遷移します。

`top` コンフィグモードの中で最上位の階層に移動します。

`commit` コンフィグを確定します。

`show configuration` コミット前の編集されている設定を表示します。

`show configuration running` ランニングコンフィグを表示します（コンフィグモードでも使えます）

`show network-instance default protocol ISIS MAIN interface * state`

`show network-instance default rib IPV4 ipv4-entries entry displaylevel 1` ルーティングテーブルをシンプルに表示します。

例

```text
root@R1# show network-instance default rib IPV4 ipv4-entries entry displaylevel 1
ipv4-entries entry 192.168.255.1/32
ipv4-entries entry 192.168.255.2/32
```

`show interface swp1 counters | repeat 1` 1秒に一度、インタフェースのカウンター値を表示します。


<br><br><br>

## SRv6

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

このローカルSIDをloopback0に割り当てたいけど、subinterface 0に複数のIPv6アドレスは割り当てられません。

かといって、subinterface 1を作ろうとすると怒られます。

これは意味がわからないのですが、ソフトインタフェースなのだからloopback 1を作れってことかもしれません。

<br>

## L3VPN over SRv6

L3VPN over SRv6を検証します。

<br>

![構成](/assets/arcos_l3vpn.png)

<br>

踏み台サーバに置いた設定をZero Touch Provisioningで配信します。

[P1.cfg](/arcos/config/P1.cfg)　　[P2.cfg](/arcos/config/P2.cfg)　　[PE11.cfg](/arcos/config/PE11.cfg)　　[PE12.cfg](/arcos/config/PE12.cfg)　　[PE13.cfg](/arcos/config/PE13.cfg)　　[PE14.cfg](/arcos/config/PE14.cfg)

<br>

重要なのはここ。

```text
network-instance vrf-1
 !
 protocol BGP vrf-1
  global sid-allocation-mode INSTANCE_SID
```

**global sid-allocation-mode** は INSTANCE_SID 以外、動きません。

もうひとつ重要なのは、IPv6アドレスのBGPネイバーには **extended-nexthop enable true** の設定が必要なこと。

RFC 8950(Advertising IPv4 Network Layer Reachability Information with an IPv6 Next Hop)を有効にする設定です。

```text
network-instance default
 protocol BGP MAIN
  neighbor 2001:db8:ffff::2
   !
   afi-safi L3VPN_IPV4_UNICAST
    extended-nexthop enable true
    exit
```

CiscoやFRRの実装はデフォルトのままで（設定しなくて）大丈夫なのですが、arcosの場合は明示的に設定しないといけません。

設定しない場合は、状態がESTABLISHEDになっても、L3VPN_IPV4_UNICASTの経路は交換してくれません。

<br><br>

## 次に試すこと

- NETCONF
- SR-MPLS
- ISIS FlexAlgo


<br><br>

## NETCONF

動いていません。

netmiko、scrapli、ncclientを試しましたが、いずれもダメです。

試しにsshでポート830に接続してみると、こうなります。

```text
iida@s400win:~/git/expt-cml/arcos$ ssh 192.168.254.1 -p 830 -l cisco
Warning: Permanently added '192.168.0.100' (ECDSA) to the list of known hosts.
Warning: Permanently added '[192.168.254.1]:830' (ECDSA) to the list of known hosts.
ArcOS (c) Arrcus, Inc.
cisco@192.168.254.1's password:
PTY allocation request failed on channel 0
Only NETCONF sessions are allowed on this port.
Connection to 192.168.254.1 closed.
```

NETCONFの場合でも、

'Only NETCONF sessions are allowed on this port.'

で切られるんだけど、jumphost経由の通信だとそうなるのかな。




<!--

system hostname <ルータ名>
system aaa authentication admin-user admin-password

system clock timezone-name Asia/Tokyo
system ssh-server enable true
system ssh-server permit-root-login true
system aaa authentication user cisco role SYSTEM_ROLE_ADMIN password cisco123
exit
system aaa authentication user admin role SYSTEM_ROLE_ADMIN password <パスワード>
exit

interface loopback0
enabled true
mtu 3000
subinterface 0
enabled true
ipv4 enabled true
ipv4 address 10.0.255.{{ ルータ番号 }} prefix-length 32
exit
ipv6 enabled true
ipv6 address 2001:db8:ffff::{{ ルータ番号 }} prefix-length 128
exit
top


interface swp1 enabled true
exit

interface swp2 enabled true
exit

interface swp3 enabled true
exit

interface swp4 enabled true
exit

interface swp1,2,3,4
enabled true
mtu 3000
subinterface 0
ipv4 enabled false
no ipv4 address
ipv6 enabled true
ipv6 router-advertisement suppress true

top
network-instance default
srv6 locator MAIN
locator-node-length 16
prefix fd00:0:0:{{ ルータ番号 }}::/64
top

top
network-instance default
protocol ISIS MAIN
global net 49.0000.0000.0000.00{{ ルータ番号2桁 }}.00
global graceful-restart enabled true

global af IPV6 UNICAST enabled true
exit

global af IPV4 UNICAST enabled true
exit

global srv6 enabled true

global srv6 locator MAIN
exit

level 1 enabled true
exit

level 2 enabled false
exit

top
network-instance default protocol ISIS MAIN
interface swp1
enabled true
network-type POINT_TO_POINT

af IPV6 UNICAST enabled true
exit

af IPV4 UNICAST enabled true
exit

level 1 enabled true
exit

level 2 enabled false
exit


top
network-instance default protocol ISIS MAIN
interface swp2
enabled true
network-type POINT_TO_POINT

af IPV6 UNICAST enabled true
exit

af IPV4 UNICAST enabled true
exit

level 1 enabled true
exit

level 2 enabled false
exit

top
network-instance default protocol ISIS MAIN
interface swp3
enabled true
network-type POINT_TO_POINT

af IPV6 UNICAST enabled true
exit

af IPV4 UNICAST enabled true
exit

level 1 enabled true
exit

level 2 enabled false
exit


top
network-instance default protocol ISIS MAIN
interface swp4
enabled true
network-type POINT_TO_POINT

af IPV6 UNICAST enabled true
exit

af IPV4 UNICAST enabled true
exit

level 1 enabled true
exit

level 2 enabled false
exit


top
network-instance default protocol ISIS MAIN

interface loopback0
enabled true
passive true

af IPV6 UNICAST enabled true
exit

af IPV4 UNICAST enabled true
exit

level 1 enabled true
exit

level 2 enabled false
exit



PルータのBGP設定

network-instance default protocol BGP MAIN

global router-id 10.0.255.{{ ルータ番号 }}
global as 65000
global cluster-id 0.0.0.1
global graceful-restart enabled true
global srv6 locator MAIN
global sid-allocation-mode INSTANCE_SID

global afi-safi L3VPN_IPV6_UNICAST
exit

global afi-safi L3VPN_IPV4_UNICAST
exit

neighbor 2001:db8:ffff::{{ もう一台のPルータのルータ番号 }}
peer-as 65000
transport local-address 2001:db8:ffff::{{ 自分のルータ番号 }}

afi-safi L3VPN_IPV6_UNICAST
extended-nexthop enable true
exit

afi-safi L3VPN_IPV4_UNICAST
extended-nexthop enable true
exit

top
network-instance default protocol BGP MAIN
peer-group pe
transport local-address 2001:db8:ffff::{{ 自分のルータ番号 }}
peer-as 65000
route-reflector route-reflector-client true
afi-safi L3VPN_IPV4_UNICAST
extended-nexthop enable true
exit
afi-safi L3VPN_IPV6_UNICAST
extended-nexthop enable true
exit

top
network-instance default protocol BGP MAIN
neighbor 2001:db8:ffff::11
peer-group pe
exit

neighbor 2001:db8:ffff::12
peer-group pe
exit

neighbor 2001:db8:ffff::12
peer-group pe
exit

neighbor 2001:db8:ffff::13
peer-group pe
exit


PEルータのBGP設定

top
network-instance default protocol BGP MAIN
global router-id 10.0.255.{{ ルータ番号 }}
global as 65000
global graceful-restart enabled true
global srv6 locator MAIN
global sid-allocation-mode INSTANCE_SID

global afi-safi L3VPN_IPV6_UNICAST
exit

global afi-safi L3VPN_IPV4_UNICAST
exit

peer-group rr
transport local-address 2001:db8:ffff::{{ 自分のルータ番号 }}
peer-as 65000

afi-safi L3VPN_IPV4_UNICAST
extended-nexthop enable true
exit

afi-safi L3VPN_IPV6_UNICAST
extended-nexthop enable true
exit

top
network-instance default protocol BGP MAIN

neighbor 2001:db8:ffff::1
peer-group rr
exit

neighbor 2001:db8:ffff::2
peer-group rr
exit


設定を外にバックアップ

root@PE11# show running-config | save PE11.cfg

root@PE11# scp vrf management PE11.cfg cisco@192.168.254.100:
The authenticity of host '192.168.254.100 (192.168.254.100)' can't be established.
ED25519 key fingerprint is SHA256:sPuXcDlKojPQueUCXuNdL3MzagY3GGF5187hjFMvYZk.
This key is not known by any other names.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '192.168.254.100' (ED25519) to the list of known hosts.
cisco@192.168.254.100's password:
PE11.cfg                                      100% 4856     6.1MB/s   00:00




NETCONF

注意：ArcOSでは、部分的な設定変更はできない
注意：デフォルトのポートは830
注意：デフォルトのアイドルタイムアウトは0なので、タイムアウトしない

system netconf-server enable true
system netconf-server transport ssh enable true
system netconf-server transport ssh timeout 60

-->