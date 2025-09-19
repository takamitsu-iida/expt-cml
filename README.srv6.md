# SRv6

FRR(Docker)を使ってSRv6のL3VPNを検証します。

[README.create_custom_docker.md](/README.create_custom_docker.md) に従ってFRRをインストールしたDockerイメージを作成してCMLに登録します。

> [!NOTE]
>
> CML2.9に同梱されているFRR(Docker)ではSRv6を動かすことはできません。
> FRRをコンパイルして作成してください。

<br>

## ラボ構成

スクリプト [cml_create_srv6_docker_lab.py](bin/cml_create_srv6_docker_lab.py) を使ってCML内にラボを自動生成します。

<br>

![ラボ構成](/assets/srv6_docker_lab.png)

<br>

## Linuxの設定

FRRでVRFを作ることはできません。

FRR(Docker)の設定ファイルboot.shにて以下を実行しています。

```bash
# create vrf for CE router
ip link add CE type vrf table 1001
ip link set dev CE up
ip link set dev eth2 master CE
```

コンテナ起動時に以下のsysctlを設定しています。

```bash
--sysctl net.ipv4.conf.all.rp_filter=0
--sysctl net.ipv4.conf.default.rp_filter=0
--sysctl net.ipv6.conf.all.keep_addr_on_down=1
--sysctl net.ipv6.conf.all.forwarding=1
--sysctl net.ipv6.route.skip_notify_on_dev_down=1
--sysctl net.ipv6.seg6_flowlabel=1
--sysctl net.ipv6.conf.all.seg6_enabled=1
--sysctl net.ipv6.conf.default.seg6_enabled=1
--sysctl net.ipv6.conf.all.seg6_require_hmac=0
--sysctl net.vrf.strict_mode=1
```

<br>

## ルータの設定

スクリプト内で自動生成しています。

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

<br>

## 疎通確認

CE101からpingします。

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

カプセル化するときの設定で、以下を設定した場合の
CE101からCE103へのping通信の[パケットキャプチャ](/assets/srv6-from-ce101-to-ce103-red.pcap)

IPv6ヘッダにSRはありません。

```text
  encap-behavior H_Encaps_Red
```

設定しなかった場合（デフォルト動作）の
CE101からCE103へのping通信の[パケットキャプチャ](/assets/srv6-from-ce101-to-ce103.pcap)

IPv6ヘッダにSRが登場します。

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


<br><br><br>

# FRRの設定

PEルータにVRFを作成して、エンド・エンドでIPv4通信できるようにします。

<br>

## VRF作成

FRRはVRFを作成しません。Linuxで作成します。

FRR(Docker)を起動するときに作成することにします。









<br>

ループバックのIPv6アドレスはロケータのノードSIDと同じものを割り当てます。

IPv6アドレスは複数持てますので、管理用アドレスとノードSID、両方を設定します。

たとえばロケータがfd00:1::/48の場合、ループバックにはfd00:1::/128を設定する。
これでノードSIDにpingが通るようになり、トンネルの端点のアドレスとしても使えるようになる。

<br>



## ロケータ定義

```text
!
segment-routing
 srv6
  locators
   locator MAIN
    prefix fd00:1:1::/48
    format usid-f3216
   exit
   !
  exit
  !
 exit
 !
exit
!
```

MAINというのは、このロケータにつけた名称です。ロケータは複数持てます。

<br>

## ロケータをISISで配信

ロケータはIPv6のプレフィクスと同等ですので、ルーティングプロトコルで配信しておけば、SRv6に関心のないルータにもルーティングテーブルに反映されます。

FRRのISISの設定では、redistributeではなく、segment-routing srv6で設定します。

```text
!
router isis 1
 is-type level-1
 net 49.0001.0000.0000.0001.00
 segment-routing srv6
  locator MAIN
 exit
exit
!
```

これで/48の経路が配信されます。

<br>

## SIDを確認

ロケータを作成すると、そのルータの中には最低限のSIDが作られます。

`show segment-routing srv6 sid`

```text
P1# show segment-routing srv6 sid
 SID              Behavior    Context             Daemon/Instance    Locator    AllocationType
 ---------------------------  ------------------  -----------------  ---------  ----------------
 fd00:1:1::       uN          -                   isis(0)            MAIN       dynamic
 fd00:1:1:e000::  uA          Interface 'eth0'    isis(0)            MAIN       dynamic
 fd00:1:1:e001::  uA          Interface 'eth1'    isis(0)            MAIN       dynamic
 fd00:1:1:e002::  uA          Interface 'eth2'    isis(0)            MAIN       dynamic
 fd00:1:1:e003::  uA          Interface 'eth3'    isis(0)            MAIN       dynamic
```

先頭32ビットの fd00:1 はSRv6を形成するドメインで共通のプレフィクスです。

このルータのノード部16ビットは 1 としています。

その結果、ロケータはfd00:1:1::/48となります。

SID fd00:1:1:: はロケータと同じです。uN(Endpoint)です。ルーティングテーブルを見て中継します。

SID fd00:1:1:e000:: はuAで、eth0に中継します。

SID fd00:1:1:e001:: はuAで、eth1に中継します。

SID fd00:1:1:e002:: はuAで、eth2に中継します。

SID fd00:1:1:e003:: はuAで、eth3に中継します。

全ルータにロケータを設定して、ISISで配信したとしても、これら個々のSIDがISISで配信されることはありません。
ISISではあくまで/48の経路情報が流れてくるだけです。

<br><br>

## Traffic Steering into SRv6


CE101からCE102への最短経路は `CE101---PE11---P1---PE13---CE102` です。

これをPE11で曲げてみます。

スタティックルートを書きます。

指定しているのはSIDではないループバックアドレスになっているところが気になりますが、こうしないと動きませんでした。

```text
ip route 10.0.102.0/24 lo segments 2001:db8:ffff::1/2001:db8:ffff::12/2001:db8:ffff::2/2001:db8:ffff::13
```

これで `CE101---PE11---P1---PE12---P2---PE13---CE102` という順路になります。



> [!NOTE]
>
> なぜSIDを指定すると動かないんだろう？？？
>
> ループバックのアドレスをSIDの中から採番すればいい？？？







## Static

- uN (Shift and forward)
- uA (Shift and L3 cross-connect)
- uDT4 (Decapsulation and IPv4 table lookup)
- uDT6 (Decapsulation and IPv6 table lookup)
- uDT46 (Decapsulation and IP table lookup)

```text
!
segment-routing
    static-sids
      sid fd00:aaaa:1::/48 locator MAIN behavior uN
      sid fd00:aaaa:1:ff10::/64 locator MAIN behavior uDT4 vrf Vrf10
      sid fd00:aaaa:1:ff20::/64 locator MAIN behavior uDT6 vrf Vrf20
      sid fd00:aaaa:1:ff30::/64 locator MAIN behavior uDT46 vrf Vrf30
      sid fd00:aaaa:1:ff40::/64 locator MAIN behavior uA interface eth1
```


## BGP L3VPN

```text
router bgp 65001
  bgp router-id 192.168.255.1
  no bgp ebgp-requires-policy
  neighbor 2001:db8:ffff::2 remote-as 65001
  neighbor 2001:db8:ffff::2 capability extended-nexthop
  ...
  address-family ipv4 vpn
    neighbor 2001:db8:ffff::2 activate
    exit-address-family
  !
  address-family ipv6 vpn
    neighbor 2001:db8:ffff::2 activate
    exit-address-family
  !
!
router bgp 65001 vrf vrff10
  bgp router-id 192.168.255.1
  no bgp ebgp-requires-policy
  sid vpn per-vrf export auto
  !
  address-family ipv4 unicast
    nexthop vpn export 2001:db8:ffff::1
    rd vpn-export 2:10
    rt vpn-both 99:99
    import vpn
    export vpn
    redistribution connected
  exit-address-family
  !
  address-family ipv6 unicast
   ...


```