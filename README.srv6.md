# SRv6

FRR(Docker)を使ってSRv6のL3VPNを検証します。

<br>

## 事前準備

[README.create_custom_docker.md](/README.create_custom_docker.md) に従ってFRRをインストールしたDockerイメージを作成してCMLに登録します。

<br>

> [!NOTE]
>
> CML2.9に同梱されているFRR(Docker)ではSRv6を動かすことはできません。
> FRRをコンパイルして作成してください。

<br>

## ラボ構成

スクリプト [cml_create_srv6_docker_lab.py](bin/cml_create_srv6_docker_lab.py) を使ってラボを自動生成します。

Pルータ、PEルータはDockerコンテナで、シリアルコンソール経由でvtyshに接続できます。

また、コンテナ内でsshdを有効にしてありますので、Ubuntuを踏み台にして乗り込むこともできます。

<br>

![ラボ構成](/assets/srv6_docker_lab.png)

<br>

## Linuxの設定

FRR(Docker)でVRFを作ることはできません。

FRR(Docker)の設定ファイルboot.shにて以下を実行してCEというvrfを作成します。

PEルータのeth2はvrfに向けています。

```bash
# create vrf for CE router
ip link add CE type vrf table 1001
ip link set dev CE up
ip link set dev eth2 master CE
```

<br><br>

SRv6を動かすためにコンテナ起動時に以下のsysctlを設定しています（[ノード定義ファイル](/frr/cml_node_definition.yaml)を参照）。

```bash
net.ipv4.conf.all.rp_filter=0
net.ipv4.conf.default.rp_filter=0
net.ipv6.conf.all.keep_addr_on_down=1
net.ipv6.conf.all.forwarding=1
net.ipv6.route.skip_notify_on_dev_down=1
net.ipv6.seg6_flowlabel=1
net.ipv6.conf.all.seg6_enabled=1
net.ipv6.conf.default.seg6_enabled=1
net.ipv6.conf.all.seg6_require_hmac=0
net.vrf.strict_mode=1
```

<br>

## ルータの設定

スクリプト内で自動生成しています。

ループバックのIPv6アドレスはノードSIDと同じものを割り当てます。

IPv6アドレスは複数持てますので、管理用アドレスとノードSID、両方を設定します。

たとえばロケータがfd00:1:1::/48の場合、ループバックにはfd00:1:1::/128を設定します。
これでノードSIDにpingが通るようになり、トンネルの端点のアドレスとしても使えるようになります。

<br>

PE11の設定

```text
!
frr version 10.4.120250905
frr defaults traditional
hostname PE11
log syslog informational
service integrated-vtysh-config
!
ip router-id 192.168.255.11
!
vrf CE
exit-vrf
!
interface eth0
 ip address 192.168.255.11 peer 192.168.255.1/32
 ip router isis 1
 ipv6 router isis 1
 isis network point-to-point
exit
!
interface eth1
 ip address 192.168.255.11 peer 192.168.255.2/32
 ip router isis 1
 ipv6 router isis 1
 isis network point-to-point
exit
!
interface eth2
 description TO CE ROUTER
 ip address 10.0.11.1/24
exit
!
interface lo
 ip address 192.168.255.11/32
 ip router isis 1
 ipv6 address 2001:db8:ffff::11/128
 ipv6 address fd00:1:11::/128
 ipv6 router isis 1
exit
!
router bgp 65000
 bgp router-id 192.168.255.11
 bgp log-neighbor-changes
 no bgp ebgp-requires-policy
 no bgp default ipv4-unicast
 neighbor P peer-group
 neighbor P remote-as internal
 neighbor fd00:1:1:: peer-group P
 neighbor fd00:1:2:: peer-group P
 !
 segment-routing srv6
  locator MAIN
 exit
 !
 address-family ipv4 vpn
  neighbor P activate
 exit-address-family
 !
 address-family ipv6 vpn
  neighbor P activate
 exit-address-family
exit
!
router bgp 65000 vrf CE
 bgp router-id 192.168.255.11
 bgp log-neighbor-changes
 no bgp ebgp-requires-policy
 no bgp default ipv4-unicast
 !
 address-family ipv4 unicast
  redistribute connected
  sid vpn export auto
  rd vpn export 65000:101
  rt vpn both 65000:101
  export vpn
  import vpn
 exit-address-family
exit
!
router isis 1
 is-type level-1
 net 49.0001.0000.0000.0011.00
 segment-routing srv6
  locator MAIN
 exit
exit
!
segment-routing
 srv6
  encapsulation
   source-address fd00:1:11::
  exit
  locators
   locator MAIN
    prefix fd00:1:11::/48
    behavior usid
    format usid-f3216
   exit
   !
  exit
  !
 exit
 !
exit
!
end
```

<br><br>

P1ルータの設定

```text
!
frr version 10.4.120250905
frr defaults traditional
hostname P1
log syslog informational
service integrated-vtysh-config
!
ip router-id 192.168.255.1
!
interface eth0
 ip address 192.168.255.1 peer 192.168.255.11/32
 ip router isis 1
 ipv6 router isis 1
 isis network point-to-point
exit
!
interface eth1
 ip address 192.168.255.1 peer 192.168.255.12/32
 ip router isis 1
 ipv6 router isis 1
 isis network point-to-point
exit
!
interface eth2
 ip address 192.168.255.1 peer 192.168.255.13/32
 ip router isis 1
 ipv6 router isis 1
 isis network point-to-point
exit
!
interface eth3
 ip address 192.168.255.1 peer 192.168.255.14/32
 ip router isis 1
 ipv6 router isis 1
 isis network point-to-point
exit
!
interface eth4
 description MANAGEMENT
 ip address 192.168.254.1/24
 ip router isis 1
exit
!
interface lo
 ip address 192.168.255.1/32
 ip router isis 1
 ipv6 address 2001:db8:ffff::1/128
 ipv6 address fd00:1:1::/128
 ipv6 router isis 1
exit
!
router bgp 65000
 bgp router-id 192.168.255.1
 bgp log-neighbor-changes
 no bgp ebgp-requires-policy
 no bgp default ipv4-unicast
 bgp cluster-id 0.0.0.1
 neighbor P peer-group
 neighbor P remote-as internal
 neighbor PE peer-group
 neighbor PE remote-as internal
 neighbor fd00:1:2:: peer-group P
 neighbor fd00:1:11:: peer-group PE
 neighbor fd00:1:12:: peer-group PE
 neighbor fd00:1:13:: peer-group PE
 neighbor fd00:1:14:: peer-group PE
 !
 segment-routing srv6
  locator MAIN
 exit
 !
 address-family ipv4 vpn
  neighbor P activate
  neighbor PE activate
  neighbor PE route-reflector-client
 exit-address-family
 !
 address-family ipv6 vpn
  neighbor P activate
  neighbor PE activate
  neighbor PE route-reflector-client
 exit-address-family
exit
!
router isis 1
 is-type level-1
 net 49.0001.0000.0000.0001.00
 segment-routing srv6
  locator MAIN
 exit
exit
!
segment-routing
 srv6
  encapsulation
   source-address fd00:1:1::
  exit
  locators
   locator MAIN
    prefix fd00:1:1::/48
    behavior usid
    format usid-f3216
   exit
   !
  exit
  !
 exit
 !
exit
!
end
```

その他のルータはアドレスやロケータが異なるだけです。

<br>

## 疎通確認

CE101から他のCEルータにpingします。

```text
CE101# ping ip 10.0.12.102
  <cr>
CE101# ping ip 10.0.12.102
PING 10.0.12.102 (10.0.12.102): 56 data bytes
64 bytes from 10.0.12.102: seq=0 ttl=63 time=0.304 ms
64 bytes from 10.0.12.102: seq=1 ttl=63 time=1.376 ms
64 bytes from 10.0.12.102: seq=2 ttl=63 time=2.343 ms
^C
--- 10.0.12.102 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss

round-trip min/avg/max = 0.304/1.341/2.343 ms
CE101# ping ip 10.0.13.103
PING 10.0.13.103 (10.0.13.103): 56 data bytes
64 bytes from 10.0.13.103: seq=0 ttl=63 time=0.638 ms
64 bytes from 10.0.13.103: seq=1 ttl=63 time=2.256 ms
64 bytes from 10.0.13.103: seq=2 ttl=63 time=1.996 ms
^C
--- 10.0.13.103 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
round-trip min/avg/max = 0.638/1.630/2.256 ms

CE101# ping ip 10.0.14.104
PING 10.0.14.104 (10.0.14.104): 56 data bytes
64 bytes from 10.0.14.104: seq=0 ttl=63 time=0.617 ms
64 bytes from 10.0.14.104: seq=1 ttl=63 time=2.233 ms
64 bytes from 10.0.14.104: seq=2 ttl=63 time=2.149 ms
^C
--- 10.0.14.104 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
round-trip min/avg/max = 0.617/1.666/2.233 ms
CE101#
```

<br>

## パケットキャプチャ

`encap-behavior H_Encaps_Red` を設定した場合のCE101からCE103へのping通信の[パケットキャプチャ](/assets/srv6-from-ce101-to-ce103-red.pcap)

IPv6ヘッダにSRはありません。

<br>

`encap-behavior H_Encaps_Red` を設定しなかった場合（デフォルト動作）のCE101からCE103へのping通信の[パケットキャプチャ](/assets/srv6-from-ce101-to-ce103.pcap)

IPv6ヘッダにSRが登場します。

<br>

<br>

## SIDを確認

`show segment-routing srv6 sid`

P11で実行した場合

```text
PE11# show segment-routing srv6 sid
 SID               Behavior    Context             Daemon/Instance    Locator    AllocationType
 ----------------------------  ------------------  -----------------  ---------  ----------------
 fd00:1:11::       uN          -                   isis(0)            MAIN       dynamic
 fd00:1:11:e000::  uDT4        VRF 'CE'            bgp(0)             MAIN       dynamic
 fd00:1:11:e001::  uA          Interface 'eth0'    isis(0)            MAIN       dynamic
 fd00:1:11:e002::  uA          Interface 'eth1'    isis(0)            MAIN       dynamic
```

<br>

## VRF経路を確認

`show ip route vrf <VRF NAME>`

PE11で実行した場合

```text
PE11# show ip route vrf CE
Codes: K - kernel route, C - connected, L - local, S - static,
       R - RIP, O - OSPF, I - IS-IS, B - BGP, E - EIGRP, N - NHRP,
       T - Table, v - VNC, V - VNC-Direct, A - Babel, F - PBR,
       f - OpenFabric, t - Table-Direct,
       > - selected route, * - FIB route, q - queued, r - rejected, b - backup
       t - trapped, o - offload failure

IPv4 unicast VRF CE:
C>* 10.0.11.0/24 is directly connected, eth2, weight 1, 01:38:41
L>* 10.0.11.1/32 is directly connected, eth2, weight 1, 01:38:41
B>  10.0.12.0/24 [200/0] via 192.168.255.12 (vrf default) (recursive), label 917504, seg6 fd00:1:12:e000::, encap behavior H.Encaps.Red, weight 1, 01:38:07
  *                        via 192.168.255.1, eth0 (vrf default) onlink, label 917504, seg6 fd00:1:12:e000::, encap behavior H.Encaps.Red, weight 1, 01:38:07
  *                        via 192.168.255.2, eth1 (vrf default) onlink, label 917504, seg6 fd00:1:12:e000::, encap behavior H.Encaps.Red, weight 1, 01:38:07
                         via 192.168.255.12 (vrf default) (recursive), label 917504, seg6 fd00:1:12:e000::, encap behavior H.Encaps.Red, weight 1, 01:38:07
                           via 192.168.255.1, eth0 (vrf default) onlink, label 917504, seg6 fd00:1:12:e000::, encap behavior H.Encaps.Red, weight 1, 01:38:07
                           via 192.168.255.2, eth1 (vrf default) onlink, label 917504, seg6 fd00:1:12:e000::, encap behavior H.Encaps.Red, weight 1, 01:38:07
B>  10.0.13.0/24 [200/0] via 192.168.255.13 (vrf default) (recursive), label 917504, seg6 fd00:1:13:e000::, encap behavior H.Encaps.Red, weight 1, 01:38:03
  *                        via 192.168.255.1, eth0 (vrf default) onlink, label 917504, seg6 fd00:1:13:e000::, encap behavior H.Encaps.Red, weight 1, 01:38:03
  *                        via 192.168.255.2, eth1 (vrf default) onlink, label 917504, seg6 fd00:1:13:e000::, encap behavior H.Encaps.Red, weight 1, 01:38:03
                         via 192.168.255.13 (vrf default) (recursive), label 917504, seg6 fd00:1:13:e000::, encap behavior H.Encaps.Red, weight 1, 01:38:03
                           via 192.168.255.1, eth0 (vrf default) onlink, label 917504, seg6 fd00:1:13:e000::, encap behavior H.Encaps.Red, weight 1, 01:38:03
                           via 192.168.255.2, eth1 (vrf default) onlink, label 917504, seg6 fd00:1:13:e000::, encap behavior H.Encaps.Red, weight 1, 01:38:03
B>  10.0.14.0/24 [200/0] via 192.168.255.14 (vrf default) (recursive), label 917504, seg6 fd00:1:14:e000::, encap behavior H.Encaps.Red, weight 1, 01:37:59
  *                        via 192.168.255.1, eth0 (vrf default) onlink, label 917504, seg6 fd00:1:14:e000::, encap behavior H.Encaps.Red, weight 1, 01:37:59
  *                        via 192.168.255.2, eth1 (vrf default) onlink, label 917504, seg6 fd00:1:14:e000::, encap behavior H.Encaps.Red, weight 1, 01:37:59
                         via 192.168.255.14 (vrf default) (recursive), label 917504, seg6 fd00:1:14:e000::, encap behavior H.Encaps.Red, weight 1, 01:37:59
                           via 192.168.255.1, eth0 (vrf default) onlink, label 917504, seg6 fd00:1:14:e000::, encap behavior H.Encaps.Red, weight 1, 01:37:59
                           via 192.168.255.2, eth1 (vrf default) onlink, label 917504, seg6 fd00:1:14:e000::, encap behavior H.Encaps.Red, weight 1, 01:37:59
PE11#
```

<br>

## VRFのBGPテーブルを確認

`show ip bgp vrf CE detail`

PE11で実行した場合

```text
PE11# show ip bgp vrf CE detail
BGP table version is 4, local router ID is 192.168.255.11, vrf id 2
Default local pref 100, local AS 65000
BGP routing table entry for 10.0.11.0/24, version 1
Paths: (1 available, best #1, vrf CE)
  Not advertised to any peer
  Local
    0.0.0.0 from 0.0.0.0 (192.168.255.11)
      Origin incomplete, metric 0, weight 32768, valid, sourced, best (First path received)
      Last update: Fri Oct  3 22:14:05 2025
BGP routing table entry for 10.0.12.0/24, version 2
Paths: (2 available, best #1, vrf CE)
  Not advertised to any peer
  Imported from 65000:101:10.0.12.0/24
  Local
    192.168.255.12 (metric 30) from 0.0.0.0 (192.168.255.11) vrf default(0) announce-nh-self
      Origin incomplete, metric 0, localpref 100, valid, sourced, local, multipath, best (Neighbor IP)
      Extended Community: RT:65000:101
      Originator: 192.168.255.12, Cluster list: 0.0.0.1
      Remote label: 917504
      Remote SID: fd00:1:12::
      Last update: Fri Oct  3 22:14:40 2025
BGP routing table entry for 10.0.12.0/24, version 2
Paths: (2 available, best #1, vrf CE)
  Not advertised to any peer
  Imported from 65000:101:10.0.12.0/24
  Local
    192.168.255.12 (metric 30) from 0.0.0.0 (192.168.255.11) vrf default(0) announce-nh-self
      Origin incomplete, metric 0, localpref 100, valid, sourced, local, multipath
      Extended Community: RT:65000:101
      Originator: 192.168.255.12, Cluster list: 0.0.0.1
      Remote label: 917504
      Remote SID: fd00:1:12::
      Last update: Fri Oct  3 22:14:40 2025
BGP routing table entry for 10.0.13.0/24, version 3
Paths: (2 available, best #1, vrf CE)
  Not advertised to any peer
  Imported from 65000:101:10.0.13.0/24
  Local
    192.168.255.13 (metric 30) from 0.0.0.0 (192.168.255.11) vrf default(0) announce-nh-self
      Origin incomplete, metric 0, localpref 100, valid, sourced, local, multipath, best (Neighbor IP)
      Extended Community: RT:65000:101
      Originator: 192.168.255.13, Cluster list: 0.0.0.1
      Remote label: 917504
      Remote SID: fd00:1:13::
      Last update: Fri Oct  3 22:14:43 2025
BGP routing table entry for 10.0.13.0/24, version 3
Paths: (2 available, best #1, vrf CE)
  Not advertised to any peer
  Imported from 65000:101:10.0.13.0/24
  Local
    192.168.255.13 (metric 30) from 0.0.0.0 (192.168.255.11) vrf default(0) announce-nh-self
      Origin incomplete, metric 0, localpref 100, valid, sourced, local, multipath
      Extended Community: RT:65000:101
      Originator: 192.168.255.13, Cluster list: 0.0.0.1
      Remote label: 917504
      Remote SID: fd00:1:13::
      Last update: Fri Oct  3 22:14:43 2025
BGP routing table entry for 10.0.14.0/24, version 4
Paths: (2 available, best #1, vrf CE)
  Not advertised to any peer
  Imported from 65000:101:10.0.14.0/24
  Local
    192.168.255.14 (metric 30) from 0.0.0.0 (192.168.255.11) vrf default(0) announce-nh-self
      Origin incomplete, metric 0, localpref 100, valid, sourced, local, multipath, best (Neighbor IP)
      Extended Community: RT:65000:101
      Originator: 192.168.255.14, Cluster list: 0.0.0.1
      Remote label: 917504
      Remote SID: fd00:1:14::
      Last update: Fri Oct  3 22:14:47 2025
BGP routing table entry for 10.0.14.0/24, version 4
Paths: (2 available, best #1, vrf CE)
  Not advertised to any peer
  Imported from 65000:101:10.0.14.0/24
  Local
    192.168.255.14 (metric 30) from 0.0.0.0 (192.168.255.11) vrf default(0) announce-nh-self
      Origin incomplete, metric 0, localpref 100, valid, sourced, local, multipath
      Extended Community: RT:65000:101
      Originator: 192.168.255.14, Cluster list: 0.0.0.1
      Remote label: 917504
      Remote SID: fd00:1:14::
      Last update: Fri Oct  3 22:14:47 2025

Displayed 4 routes and 7 total paths
PE11#
```


<br><br>

## Traffic Steering into SRv6

スタティックルートで通る場所を設定できるけど、万能なものではなさそう。

PE11にて、

```text
ip route 192.168.255.13 255.255.255.255 lo segments fd00:1:1::
```

とすると、P1のuN（fd00:1:1::）を経由したSRv6パケットで送信されます。

さらに、このように書けば、PE11→P1→PE12という順路をたどります。

```text
ip route 192.168.255.13/32 lo segments fd00:1:1::/fd00:1:12::
```

でも、これは動きません。

```text
ip route 192.168.255.13/32 lo segments fd00:1:1::/fd00:1:12:: encap-behavior H_Encaps_Red
```

<br><br><br><br><br><br><br><br>

## SIDの構造

SRv6におけるSegment ID (SID)はIPv6アドレスと同じ形式をとりますが、意味合いは違います。

```text
1111:2222:3333:4444 : 5555:6666:7777:8888
------------------    -------------------
locator               function
```

- locatorは、そのノードに到達するための経路情報で、ルータに割り当てるIPv6のサブネットと同等です。
- functionは、そのノードで実行されるアクション、サービスの番号です

ロケータはさらに次のようにブロック部とノード部に別れます。

```text
1111 : 2222 : 3333 : 4444 : 5555 : 6666 : 7777 : 8888
-----------   ----   ----   ----
Block         NodeID Func   Argument
```

ブロック部はSRv6ドメインで同じ値です。
言い換えると、ドメインを分割したときにはブロック部の値を変更します。
SRv6ドメイン同士を接続したときの経路情報の交換は、このブロック部の情報だけをお互いに交換すればいいことになります。

ノード部は、SRv6ドメイン内におけるノードを識別する部分になります。ドメイン内ではノードごとに異なるノード部を持ちます。

Full-lengthのSIDはIPv6アドレスと同じフォーマットですので128ビットの長さを持っていますが、実のところ冗長な部分が多く、パケットの中に埋め込む情報としては長すぎです。

パケットに埋め込むことを想定して、本当に必要な情報だけに絞り込んでサイズを小さくしたのがマイクロセグメント（uSID）です。

<br>

## F3216フォーマット

F3216は、ブロック部が32ビット、uSIDが16ビットのフォーマットです。ルータにおけるロケータの定義は32+16=48なので /48 になります。

先頭32ビットのブロック部はSRv6を形成するドメイン内で共通の値です。
ローカルな環境であれば `fcxx:xxxx` もしくは `fdxx:xxxx` の中から採番されることが多いです。

SIDの16ビット部分は、特定のルータやそのルータ内で定義されるサービスを識別する役割を担います。

IPv6アドレスの形式には最大6個のuSIDを格納できます。

```text
fc00:0001 : 0001 : 0002 : 0003 : 0004 : 0005 : 0006
---------   ----   ----   ----   ----   ----   ----
block       node1  node2  node3  node4  node5  node6
```

6個以下のuSIDですむのであればSRヘッダを使うことなく、宛先IPv6アドレスだけでuSIDのリストを表現できます。

7個以上のuSIDを格納するときにはSRヘッダを使う必要がでてきます。

<br>

## behaviors

| name                     | behavior            |
| ------------------------ | ------------------- |
| End uN                   | Endpoint [Node SID] |
| End.X uA                 | Endpoint with Layer-3 cross-connect [Adj SID] |
| End.B6.Insert uB6.Insert | Endpoint bound to an SRv6 policy [BSID] |
| End.B6.Encap uB6.Encaps  | Endpoint bound to an SRv6 encapsulation policy [BSID] |
| End.DX6 uDX6             | Endpoint with decapsulation and IPv6 cross-connect [L3VPN Per-CE] |
| End.DX4 uDX4             | Endpoint with decapsulation and IPv4 cross-connect [L3VPN Per-CE] |
| End.DT6 uDT6             | Endpoint with decapsulation and specific IPv6 table lookup [L3VPN Per-VRF] |
| End.DT4 uDT4             | Endpoint with decapsulation and specific IPv4 table lookup [L3VPN Per-VRF] |
| End.DT46 uDT46           | Endpoint with decapsulation and specific IP table lookup [L3VPN Per-VRF] |
| End.DX2 uDX2             | Endpoint with decapsulation and L2 cross-connect [E-LINE] |
| End.DT2U/M uDT2U/M       | Endpoint with decapsulation and L2 unicast lookup / flooding [E-LAN] |
| End.DTM uDTM             | Endpoint with decapsulation and MPLS table lookup [Interworking] |
| H.Insert / H.Encaps      | Headend with Insertion / Encapsulation of / into an SRv6 policy [TiLFA] |
| H. Encaps.L2             | H.Encaps Applied to Received L2 Frames [L2 Port Mode] |
| H.Encaps.M               | H.Encaps Applied to MPLS Label Stack [Interworking] |

<br>

### END

full-length SID

ENDという名前ですが、実際には中継動作です

- パケットを受信したら、ルーティングヘッダのSegment Leftを-1して、宛先IPv6アドレスを次のSIDに変更
- 自分自身の**ルーティングテーブルを参照して転送**

<br>

### uN

uSID

- 宛先IPv6アドレスから自分自身のuSIDを取り除いて左にシフトします
- 一番右を0x0000でパディングします（End-of-Carrier)
- このようにして変更した宛先アドレスに向けて自分のルーティングテーブルに従って転送します

<br>

### END.X

full-length SID

- パケットを受信したら、ルーティングヘッダのSegment Leftを-1して、宛先IPv6アドレスを次のSIDに変更
- **特定のインタフェース**にパケットを転送

<br>

### uA

uSID

- 宛先IPv6アドレスから自分自身のuSIDを取り除いて左にシフトします
- 一番右を0x0000でパディングします（End-of-Carrier)
- **特定のインタフェース**にパケットを転送

<br>

### END.DX4 END.DX6 END.DX2

full-length SID

Decapsulation(カプセル化解除) and Xconnect(特定のインタフェースに転送)の頭文字を取ってDXです。

SRv6ドメインから出ていく通信の中継処理、すなわちVPNサービスです。

PEルータにパケットが到着したときにはルーティングヘッダのSegment Leftは0のはずです。

- パケットを受信したらIPv6ヘッダを取り除きます
- 特定のインタフェースに向けてパケットを転送します

<br>

### uDX

uSID

Decapsulation(カプセル化解除) and Xconnect(特定のインタフェースに転送)の頭文字を取ってDXです。

PEルータにパケットが到着したときには、uSIDキャリアの最後のノードのはずです。

- パケットを受信したらIPv6ヘッダを取り除きます
- 特定のインタフェースに向けてパケットを転送します

<br>

### END.DT4 END.DT6

full-length SID

Decapsulation(カプセル化解除) and Table-lookup(テーブル参照)の頭文字を取ってDTです。

SRv6ドメインから出ていく通信の中継処理、すなわちVPNサービスです。

PEルータにパケットが到着したときにはルーティングヘッダのSegment Leftは0のはずです。

- パケットを受信したらIPv6ヘッダを取り除きます
- 特定のVRFテーブルを検索してパケットを転送します

<br>

### uDT

uSID

Decapsulation(カプセル化解除) and Table-lookup(テーブル参照)の頭文字を取ってDTです。

PEルータにパケットが到着したときには、uSIDキャリアの最後のノードのはずです。

- パケットを受信したらIPv6ヘッダを取り除きます
- 特定のVRFテーブルを検索してパケットを転送します

<br>

## データプレーン

uSIDの場合、宛先IPv6アドレスの中にSIDの情報を詰め込みます。

パケットを受信したら宛先IPv6アドレスの中の自分のuSIDを削除して左にシフト、右には0x0000をパディングして宛先アドレスを変えていきますので、
ルータを経由するたびに宛先IPv6アドレスが変わっていきます。

宛先アドレスの形式はあくまでIPv6のままですので、途中にSRv6を理解しないルータがいても大丈夫です。宛先をみて中継するだけです。

通常SRv6ドメインのエッジルータ（PEルータ）では何かしらのサービスを実行しますので、uDTやuDXなど、PEルータ自身が決めた動作を行います。
