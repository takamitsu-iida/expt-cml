# FRR(Docker)でOpenFabricを検証する

<br>

CML2.9以降でDockerイメージが動作するようになっています。

[この手順](/README.create_frr_docker.md)で作成したFRR(Docker)を使ってOpenFabricの検証を行います。

<br><br>

## ラボ構成

スクリプト [/bin/cml_create_openfabric_docker_lab.py](/bin/cml_create_openfabric_docker_lab.py) を使ってCML内にラボを自動生成します。

<br>

![ラボ構成](/assets/openfabric_docker_lab.png)

<br><br>

## R1のルーティングテーブル

**IPv4のルーティングテーブル**

```bash
R1# show ip route
Codes: K - kernel route, C - connected, L - local, S - static,
       R - RIP, O - OSPF, I - IS-IS, B - BGP, E - EIGRP, N - NHRP,
       T - Table, v - VNC, V - VNC-Direct, A - Babel, F - PBR,
       f - OpenFabric, t - Table-Direct,
       > - selected route, * - FIB route, q - queued, r - rejected, b - backup
       t - trapped, o - offload failure

IPv4 unicast VRF default:
L * 192.168.255.1/32 is directly connected, lo, weight 1, 00:03:54
C>* 192.168.255.1/32 is directly connected, lo, weight 1, 00:03:54
f>* 192.168.255.2/32 [115/30] via 192.168.255.4, eth0 onlink, weight 1, 00:03:24
  *                           via 192.168.255.5, eth1 onlink, weight 1, 00:03:24
  *                           via 192.168.255.9, eth2 onlink, weight 1, 00:03:24
  *                           via 192.168.255.10, eth3 onlink, weight 1, 00:03:24
f>* 192.168.255.3/32 [115/30] via 192.168.255.4, eth0 onlink, weight 1, 00:03:24
  *                           via 192.168.255.5, eth1 onlink, weight 1, 00:03:24
  *                           via 192.168.255.9, eth2 onlink, weight 1, 00:03:24
  *                           via 192.168.255.10, eth3 onlink, weight 1, 00:03:24
f>* 192.168.255.4/32 [115/20] via 192.168.255.4, eth0 onlink, weight 1, 00:03:24
f>* 192.168.255.5/32 [115/20] via 192.168.255.5, eth1 onlink, weight 1, 00:03:24
f>* 192.168.255.6/32 [115/30] via 192.168.255.4, eth0 onlink, weight 1, 00:03:24
  *                           via 192.168.255.5, eth1 onlink, weight 1, 00:03:24
f>* 192.168.255.7/32 [115/30] via 192.168.255.4, eth0 onlink, weight 1, 00:03:04
  *                           via 192.168.255.5, eth1 onlink, weight 1, 00:03:04
f>* 192.168.255.8/32 [115/30] via 192.168.255.4, eth0 onlink, weight 1, 00:03:04
  *                           via 192.168.255.5, eth1 onlink, weight 1, 00:03:04
f>* 192.168.255.9/32 [115/20] via 192.168.255.9, eth2 onlink, weight 1, 00:03:24
f>* 192.168.255.10/32 [115/20] via 192.168.255.10, eth3 onlink, weight 1, 00:03:24
f>* 192.168.255.11/32 [115/30] via 192.168.255.9, eth2 onlink, weight 1, 00:02:58
  *                            via 192.168.255.10, eth3 onlink, weight 1, 00:02:58
f>* 192.168.255.12/32 [115/30] via 192.168.255.9, eth2 onlink, weight 1, 00:02:57
  *                            via 192.168.255.10, eth3 onlink, weight 1, 00:02:57
f>* 192.168.255.13/32 [115/30] via 192.168.255.9, eth2 onlink, weight 1, 00:02:54
  *                            via 192.168.255.10, eth3 onlink, weight 1, 00:02:54
```

<br>

**R1からR8へのping**

```bash
R1# ping 192.168.255.8
PING 192.168.255.8 (192.168.255.8): 56 data bytes
64 bytes from 192.168.255.8: seq=0 ttl=63 time=1.611 ms
64 bytes from 192.168.255.8: seq=1 ttl=63 time=0.812 ms
^C
--- 192.168.255.8 ping statistics ---
2 packets transmitted, 2 packets received, 0% packet loss
round-trip min/avg/max = 0.812/1.211/1.611 ms
```

<br>

**R1からR13へのping**

```bash
R1# ping 192.168.255.13
PING 192.168.255.13 (192.168.255.13): 56 data bytes
64 bytes from 192.168.255.13: seq=0 ttl=63 time=0.610 ms
64 bytes from 192.168.255.13: seq=1 ttl=63 time=0.710 ms
^C
--- 192.168.255.13 ping statistics ---
2 packets transmitted, 2 packets received, 0% packet loss
round-trip min/avg/max = 0.610/0.660/0.710 ms
```

<br>

**IPv6のルーティングテーブル**

```bash
R1# show ipv6 route
Codes: K - kernel route, C - connected, L - local, S - static,
       R - RIPng, O - OSPFv3, I - IS-IS, B - BGP, N - NHRP,
       T - Table, v - VNC, V - VNC-Direct, A - Babel, F - PBR,
       f - OpenFabric, t - Table-Direct,
       > - selected route, * - FIB route, q - queued, r - rejected, b - backup
       t - trapped, o - offload failure

IPv6 unicast VRF default:
L * 2001:db8::1/128 is directly connected, lo, weight 1, 00:04:25
C>* 2001:db8::1/128 is directly connected, lo, weight 1, 00:04:25
f>* 2001:db8::2/128 [115/30] via fe80::4, eth0 onlink, weight 1, 00:03:55
  *                          via fe80::5, eth1 onlink, weight 1, 00:03:55
  *                          via fe80::9, eth2 onlink, weight 1, 00:03:55
  *                          via fe80::10, eth3 onlink, weight 1, 00:03:55
f>* 2001:db8::3/128 [115/30] via fe80::4, eth0 onlink, weight 1, 00:03:55
  *                          via fe80::5, eth1 onlink, weight 1, 00:03:55
  *                          via fe80::9, eth2 onlink, weight 1, 00:03:55
  *                          via fe80::10, eth3 onlink, weight 1, 00:03:55
f>* 2001:db8::4/128 [115/20] via fe80::4, eth0 onlink, weight 1, 00:03:55
f>* 2001:db8::5/128 [115/20] via fe80::5, eth1 onlink, weight 1, 00:03:55
f>* 2001:db8::6/128 [115/30] via fe80::4, eth0 onlink, weight 1, 00:03:55
  *                          via fe80::5, eth1 onlink, weight 1, 00:03:55
f>* 2001:db8::7/128 [115/30] via fe80::4, eth0 onlink, weight 1, 00:03:35
  *                          via fe80::5, eth1 onlink, weight 1, 00:03:35
f>* 2001:db8::8/128 [115/30] via fe80::4, eth0 onlink, weight 1, 00:03:35
  *                          via fe80::5, eth1 onlink, weight 1, 00:03:35
f>* 2001:db8::9/128 [115/20] via fe80::9, eth2 onlink, weight 1, 00:03:55
f>* 2001:db8::10/128 [115/20] via fe80::10, eth3 onlink, weight 1, 00:03:55
f>* 2001:db8::11/128 [115/30] via fe80::9, eth2 onlink, weight 1, 00:03:29
  *                           via fe80::10, eth3 onlink, weight 1, 00:03:29
f>* 2001:db8::12/128 [115/30] via fe80::9, eth2 onlink, weight 1, 00:03:28
  *                           via fe80::10, eth3 onlink, weight 1, 00:03:28
f>* 2001:db8::13/128 [115/30] via fe80::9, eth2 onlink, weight 1, 00:03:25
  *                           via fe80::10, eth3 onlink, weight 1, 00:03:25
C>* fe80::/64 is directly connected, eth1, weight 1, 00:04:24
R1#
```

<br>

**R1からR8へのping**

```
R1# ping ipv6 2001:db8::8
PING 2001:db8::8 (2001:db8::8): 56 data bytes
64 bytes from 2001:db8::8: seq=0 ttl=63 time=0.238 ms
64 bytes from 2001:db8::8: seq=1 ttl=63 time=0.958 ms
^C
--- 2001:db8::8 ping statistics ---
2 packets transmitted, 2 packets received, 0% packet loss
round-trip min/avg/max = 0.238/0.598/0.958 ms
```

<br>

**R1からR13へのping**

```
R1# ping 2001:db8::13
PING 2001:db8::13 (2001:db8::13): 56 data bytes
64 bytes from 2001:db8::13: seq=0 ttl=63 time=0.989 ms
64 bytes from 2001:db8::13: seq=1 ttl=63 time=0.822 ms
64 bytes from 2001:db8::13: seq=2 ttl=63 time=0.287 ms
^C
--- 2001:db8::13 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
round-trip min/avg/max = 0.287/0.699/0.989 ms
```

<br>


ルータ・ルータ間にはIPv6リンクローカルアドレスしか設定していませんが、IPv4およびIPv6ともに疎通できています。
