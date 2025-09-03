# SRv6 uSID

<br>

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

<br>

- static sidを設定するとき、behavior DT DXはdefault以外のVrfが必要


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