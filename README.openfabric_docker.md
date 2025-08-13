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

<br>

> [!NOTE]
>
> 新しいDockerイメージを作成すればよいのだと思いますが、
> CMLのDockerのイメージをカスタマイズする方法はドキュメントに書かれてなくてわからないです・・・
