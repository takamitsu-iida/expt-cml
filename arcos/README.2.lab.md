# ArcOS検証用ラボ（L3VPN over SRv6）の作成

<br>

ルータ単体では検証しずらいので、動作検証するためのネットワーク環境として L3VPN over SRv6 を構築します。

個人的に、この環境を簡単に作れると **良い装置** という印象を持ちます。

ArcOSは簡単に構築できたので、印象はとても良いです。

個人的感想

- 難しい装置 = IOS-XR
- 普通の装置 = FRR
- 簡単な装置 = ArcOS、FITELnet

<br>

![構成](/assets/arcos_l3vpn.png)

<br>

このラボ環境はPythonスクリプトで作成しますが、手順を踏む必要があるため `make` コマンドを使って省力化します。

```bash
$ make
jumphost                       踏み台サーバをCML上に作成する
upload                         踏み台サーバに設定ファイルをアップロードする（踏み台サーバの起動後に実行すること）
arcos                          arcosノードをCML上に作成する
start                          ラボを開始する
stop                           ラボを停止する
delete                         ラボを削除する
terminal                       ルータのコンソールに接続する
browse                         ブラウザにノードのコンソールURLを表示する
```

<br><br>

以下の順で実行します。

1. make jumphost
2. make start
3. make upload
4. make arcos
5. make start

<br>

まず make jumphost で踏み台サーバとなるUbuntuと外部接続、管理LAN用のスイッチを作ります。

make start で踏み台サーバを起動します。初回起動時にcloud-initでセットアップしますので少々時間がかかります。

make upload するとPythonで生成したルータのコンフィグを踏み台サーバに配置します。

make arcosでSRv6環境を追加します。

最後にもう一度make startして、ArcOSのルータを起動します。

<br><br>

各ルータはma1インタフェースをma-switchに接続していますので、初回起動時にDHCPでアドレスを取得すると共に、TFTPでその設定ファイルをダウンロードして起動します。

各ルータの設定は以下の通りです。

[P1.cfg](/arcos/config/P1.cfg)　　[P2.cfg](/arcos/config/P2.cfg)　　[PE11.cfg](/arcos/config/PE11.cfg)　　[PE12.cfg](/arcos/config/PE12.cfg)　　[PE13.cfg](/arcos/config/PE13.cfg)　　[PE14.cfg](/arcos/config/PE14.cfg)

<br><br>

## 注意事項

ハマりどころがいくつかあります。

<br>

### MTU設定

ArcOSのデフォルトでは、インタフェースのMTUが9000バイトになっていますが、CMLで動く仮想マシンはそんなに大きなパケットは受け取れないようです。

ISISのhelloはパディングを詰めてMTU長一杯のパケットを送ってきますが、そのパケットを受け取れないのでデフォルトのままでは隣接が確立できません。

MTU長は3000程度に抑えるのが良さそうです。

<br>

### ip unnumberedでルーティングできない

IPV4はループバックのアドレスをイーサネットに割り当てる、いわゆるip unnumberedを設定できます。

隣接ルータとの疎通も問題ありません。

ISISを使えば経路交換もできます。

ですが、Linuxのルーティングテーブルに反映されないため**ルータを超えた通信はできません**。

以下（↓）の例では10.0.255.11/32に関する経路情報を学習していますが、Linuxにこの経路が渡っていないため、この宛先には通信できません。

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

<br>

pingを実行しても **RTNETLINK answers: Network is unreachable** となってしまいます。

```text
root@PE12# ping 10.0.255.11
RTNETLINK answers: Network is unreachable
PING 10.0.255.11 (10.0.255.11) from 10.0.255.12 swp1: 56(84) bytes of data.
^C
--- 10.0.255.11 ping statistics ---
2 packets transmitted, 0 received, 100% packet loss, time 1017ms
```

<br>

この検証環境では、管理インタフェース(ma1)のみIPv4アドレスを割り当てて、SRv6網内はIPv6だけでルーティングするようにしています。


<br>

### VPNのSID割り当て

PEルータで作成するVRFの中でBGPを動かしますが、その中で設定する `global sid-allocation-mode` は **INSTANCE_SID** 以外、動きません。

```text
network-instance vrf-1
 !
 protocol BGP vrf-1
  global sid-allocation-mode INSTANCE_SID
```


<br>

### BGPネイバーの設定

IPv6アドレスで開くBGPネイバーには **extended-nexthop enable true** の設定が必要です。

これはRFC 8950(Advertising IPv4 Network Layer Reachability Information with an IPv6 Next Hop)を有効にする設定です。

```text
network-instance default
 protocol BGP MAIN
  neighbor 2001:db8:ffff::2
   !
   afi-safi L3VPN_IPV4_UNICAST
    extended-nexthop enable true
    exit
```

これを設定しないとネイバーの状態がESTABLISHEDになってもL3VPN_IPV4_UNICASTの経路を交換してくれません。

同様にIPv4アドレスで開いたBGPネイバーは、L3VPN_IPV6_UNICASTの経路を交換してくれません。
