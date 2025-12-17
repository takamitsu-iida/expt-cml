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

## 起動後の初期動作

CMLのダッシュボードでarcosをドラッグドロップでインスタンス化します。

コンソールを開いて、デフォルトのアカウントでログインします。

- root
- YouReallyNeedToChangeThis

ログインしたらpasswdコマンドでパスワードを変更します。


> [!NOTE]
>
> admin-userのパスワードがrootのパスワードかも？
>
> ZTPでコンフィグをダウンロードするとrootのパスワードがそれに書き換わったような？

<br>

ArcOSのシェルの起動は `cli` コマンドです。

```text
Welcome to the ArcOS CLI
root connected from 127.0.0.1 using console on R1
root@R1
```

このシェルは補完がかかるので使いやすいです。

`show version` はこんな感じです。

```text
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

<br>

上記メッセージにある通り `request system ztp stop` で停止します。

```text
root@localhost# request system ztp stop
Are you sure? This command will disable ZTP and may take several minutes (up to 10 minutes) [no,yes] yes

Initiating ZTP stop. Please do not perform any operation on the system until ZTP is stopped...
2025-11-27 09:00:33 ArcOS ztp INFO: Stopping ZTP...
```

<br>

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

<br>

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

<br>

これで設定変更できるようになりました。

<br><br>

## 設定をファイルとして保存

設定をテキストファイルに保存します。

```text
root@localhost# show running-config | save run-conf.txt
```

exitでシェルを抜けてbashに戻ると、保存したファイルを確認できます。

```bash
root@localhost:~# ls
run-conf.txt
root@localhost:~#
```

このように別ファイルに保存することはできるものの、ルータが起動時に読み込むコンフィグがどこに保存されているかは不明です。

<br><br>

## 注意事項

<br>

### MTUに注意

ArcOSのデフォルトでは、インタフェースのMTUが9000バイトになっていますが、CMLで動く仮想マシンはそんなに大きなパケットは受け取れないようです。

ISISのhelloはパディングを詰めてMTU長一杯のパケットを送ってきますが、それを受け取れないのでデフォルトのままでは隣接が確立できません。

MTU長は3000程度に抑えるのが良さそうです。

<br><br>

## ip unnumberedでルーティングできない

IPV4はループバックのアドレスをイーサネットに割り当てる、いわゆるip unnumberedを設定できます。

隣接ルータとの疎通も問題ありません。

ISISを使えばribも作れるのですが、実際にはLinuxのルーティングテーブルに反映されないので**ルーティングができません**。

こんな感じ（↓）でribにエントリができていても、実際にはLinuxに経路が渡っていないので通信できません。

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

<br><br>

## cliコマンドメモ

`config` コンフィグモードに遷移します。

`config exclusive` 排他でコンフィグモードに遷移します。

`top` コンフィグモードの中で最上位の階層に移動します。

`commit` コンフィグを確定します。

`commit confirmed <分>` 指定した時間（分）で元に戻します。config exclusiveが必須です。

`(config)# show configuration` コミット前の編集されている設定を表示します。

`show configuration running` ランニングコンフィグを表示します（コンフィグモードでも使えます）

`show configuration rollback changes` ロールバックできる過去の変更を表示します。

`(config)# rollback configuration <番号>` ロールバックします。

`(config)# load override merge <XMLファイル>` 指定したファイルの内容をマージします。

`(config)# load override override <XMLファイル>` いまの設定を全部消してから、新しいコンフィグとしてファイルの内容を読み込みます。

`(config)# load override replace <XMLファイル>` ファイルで指定した部分だけを差し替えて、残りの部分は現状を維持します。

`restart` プロセスを再起動します。

`request system reboot` 装置を再起動します。

`enter-network-instance default` defaultのインスタンスに入ります。

`exit-network-instance` インスタンスから抜けます。

`show network-instance default protocol ISIS MAIN interface * state`

`show network-instance default rib IPV4 ipv4-entries entry displaylevel 1` ルーティングテーブルをシンプルに表示します。

`show network-instance management rib IPV4 ipv4-entries entry` ma1に付いてるIPアドレスを確認します

例

```text
root@R1# show network-instance default rib IPV4 ipv4-entries entry displaylevel 1
ipv4-entries entry 192.168.255.1/32
ipv4-entries entry 192.168.255.2/32
```

`show interface swp1 counters | repeat 1` 1秒に一度、インタフェースのカウンター値を表示します。


<br><br>

## 装置へのログイン

所属しているのがadminsグループか、operatorsグループかで振る舞いが変わります。

CML上の仮想インスタンスの場合はこのような動きでした。
実際のハードウェアアプライアンスでは異なる動きになるかもしれません。

- rootでSSH接続　→　"default" vrfのbashが開きます。
- rootでコンソール接続　→　"default" vrfのbashが開きます。
- adminsグループのユーザでコンソール接続　→　CLIが開きます。
- operatorsグループのユーザでコンソール接続　→　CLIが開きます。
- adminsグループのユーザがSSH接続　→　CLIに入ります（bashコマンドでシェルも使えます）。
- operatorsグループのユーザがSSH接続　→　CLIに入ります。設定変更はできません。

<br>

ユーザrootでSSHした場合の例。bashに入ります。

```bash
cisco@jumphost:~/expt-cml/arcos$ ssh 192.168.254.1 -l root
Warning: Permanently added '192.168.254.1' (ED25519) to the list of known hosts.
ArcOS (c) Arrcus, Inc.
root@192.168.254.1's password:
root@P1:~#
root@P1:~# ls
root@P1:~# pwd
/root
```

ユーザciscoでSSHした場合の例。CLIが走ります。

```bash
cisco@jumphost:~/expt-cml/arcos$ ssh 192.168.254.1 -l cisco
Warning: Permanently added '192.168.254.1' (ED25519) to the list of known hosts.
ArcOS (c) Arrcus, Inc.
cisco@192.168.254.1's password:
Welcome to the ArcOS CLI
cisco connected from 192.168.254.100 using ssh on P1

cisco@P1# ?
Possible completions:
  bash                     Launch a bash shell
  cd                       Change working directory
  clear                    Clear domain specific information
```

ユーザoperatorでSSH接続した場合。CLIが走りますが、設定変更はできません。

```bash
isco@jumphost:~/expt-cml/arcos$ ssh 192.168.254.1 -l operator
Warning: Permanently added '192.168.254.1' (ED25519) to the list of known hosts.
ArcOS (c) Arrcus, Inc.
operator@192.168.254.1's password:
Welcome to the ArcOS CLI
User operator last logged in 2025-12-15T05:13:49.703133+00:00, to P1, from 127.0.0.1 using cli-console
operator connected from 192.168.254.100 using ssh on P1
operator@P1#

operator@P1# bash
-------------^
syntax error: expecting

operator@P1# config
-------------^
syntax error: expecting
```

<br><br><br>

# L3VPN over SRv6

<br>

L3VPN over SRv6を検証します。

<br>

![構成](/assets/arcos_l3vpn.png)

<br>

このラボはPythonスクリプトで作成しますが、手順を踏むために `make` コマンドを使います。

```bash
$ make
jumphost                       踏み台サーバをCML上に作成する
upload                         踏み台サーバに設定ファイルをアップロードする（踏み台サーバの起動後に実行すること）
arcos                          arcosノードをCML上に作成する
start                          ラボを開始する
stop                           ラボを停止する
delete                         ラボを削除する
terminal                       ルータのコンソールに接続する
```

<br>

以下の順で実行します。

1. make jumphost
2. make arcos
3. make upload
4. make start

<br>

`make upload` すると生成したルータのコンフィグを踏み台サーバに配置して、Zero Touch Provisioningで配信できるようになります。

各ルータはma1インタフェースをma-switchに接続していますので、初回起動時にDHCPでアドレスを取得すると共に、TFTPでファイルをダウンロードして起動します。

[P1.cfg](/arcos/config/P1.cfg)　　[P2.cfg](/arcos/config/P2.cfg)　　[PE11.cfg](/arcos/config/PE11.cfg)　　[PE12.cfg](/arcos/config/PE12.cfg)　　[PE13.cfg](/arcos/config/PE13.cfg)　　[PE14.cfg](/arcos/config/PE14.cfg)

<br><br>

## SRv6注意事項

重要なのはここ。

```text
network-instance vrf-1
 !
 protocol BGP vrf-1
  global sid-allocation-mode INSTANCE_SID
```

PEルータで作成するVRFの中でBGPを動かしますが、その中で設定する **global sid-allocation-mode** は INSTANCE_SID 以外、動きません。

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

これを設定しない場合は、状態がESTABLISHEDになっても、L3VPN_IPV4_UNICASTの経路は交換してくれません。

<br><br>

## NETCONF

できたこと

- SSHプロキシを経由せず、直接SSHで接続
- XML形式のコンフィグの全文取得

できなかったこと

- jump hostを経由したSSHプロキシを経由したNETCONF利用（netmiko、scrapli、ncclientいずれもダメ）
- 状態データの取得

わからないこと

- 通信の着信インタフェースやnetwork-instanceの制限はできる？？？

<br>

状態データを取得できないので、想定される使い道は、設定を丸ごと入れ替える場面で使う？

状態取得はgNMIの方が充実しています。


<br>

有効にする設定。

```text
system netconf-server enable true
```

トランスポートにSSHを指定する設定。SSHのポートは830です。設定で変更できます。

```text
system netconf-server transport ssh enable true
```

XML形式で保存する例。

```bash
cisco@jumphost:~/expt-cml/arcos$ ./nc.py get
➡️ NETCONF接続を試行中: 192.168.254.1:830 (ユーザー: cisco)
✅ NETCONFセッションが確立されました。セッションID: 61

➡️ <get-config> RPCを送信中 (ソース: <running>)...
✅ XMLパースが完了しました。ルート要素: {urn:ietf:params:xml:ns:netconf:base:1.0}rpc-reply
✅ XMLパースが完了しました。ルート要素: {urn:ietf:params:xml:ns:netconf:base:1.0}rpc-reply
✅ XML設定を保存しました: /tmp/192.168.254.1.xml
```

/tmp/192.168.254.1.xmlを手動で編集して、ホスト名を変更します。

手動で変更したXML形式のファイルを適用する例。

```bash
cisco@jumphost:~/expt-cml/arcos$ ./nc.py apply -f /tmp/192.168.254.1.xml
➡️ NETCONF接続を試行中: 192.168.254.1:830 (ユーザー: cisco)
✅ NETCONFセッションが確立されました。セッションID: 106

➡️ <edit-config> RPCを送信中...
   設定ファイル: /tmp/192.168.254.1.xml
✅ <edit-config>が成功しました

➡️ <commit> RPCを送信中...
✅ <commit>が成功しました。設定が装置に反映されました
```

ルータのコンソールには次のように表示されます。

```text
root@P1#
System message at 2025-12-15 16:08:40...
Commit performed by cisco via ssh using netconf.
root@P1#
root@PP1#
```

自動でコミットされました。

ホスト名が変更されたことでプロンプトも変化しています。

<br><br>

## RESTCONF

HTTPSを使うRESTCONFはデフォルトで有効かも？ TCPポート8009です。

暗号化されないHTTPのRESTCONFはTCPポート8008です。これはデフォルトでは動いてません。



<br><br>

## gNMI

gNMIで規定されている4種類のRPCのうち、GetとSetは動きませんでした。

動く

- Capabilities
- Subscribe

動かない

- Get
- Set

有効にする設定。

```text
system grpc-server enable true
```

有効にすると TCP 9339 で待ち受けを開始します。

デフォルトでは、通信は暗号化されません。

着信するインタフェースを指定できます。

```text
system grpc-server listen-interface ma1
```

通信するvrfを指定できます。インタフェースと両方指定したらインタフェースが優先です。

```text
system grpc-server network-instance management
```

通信を暗号化するには、追加の設定が必要です。

```text
system grpc-server transport-security true
```

通信を暗号化するのに自己証明書が使われます。デフォルトの証明書はここにあります。

- /mnt/onl/config/pki/certificate
- /mnt/onl/config/pki/key.pem

商用環境で使う場合、このファイルを差し替えるのではなく、別の証明書を指定します。

SAMPLEの間隔は最小30秒。それ以下を指定しても30秒間隔になります。

サンプルスクリプト　[gnmi.py](/arcos/gnmi.py)

実行例。

```bash
cisco@jumphost:~/expt-cml/arcos$ ./gnmi.py
✅ ルータ 192.168.254.1:9339 への接続に成功しました。

⏳ Subscribe (mode=STREAM) リクエストを送信中... (Ctrl+Cで終了)
時刻: 1765774295520372665, パス: interfaces/interface[name=swp1]/state/counters/in-octets, 値: 4684177
時刻: 1765774295520837391, パス: interfaces/interface[name=swp1]/state/counters/out-octets, 値: 4678344
時刻: 1765774325533688884, パス: interfaces/interface[name=swp1]/state/counters/out-octets, 値: 4690443
時刻: 1765774325533816253, パス: interfaces/interface[name=swp1]/state/counters/in-octets, 値: 4693290
^C

🛑 ユーザーによって処理が中断されました (Ctrl+C)。
✅ プログラムを終了します。
```

<br><br>

## 装置へのアクセス制御

初期状態でmanagementという名前のvrfが作られていますが、装置への管理アクセスはmanagement vrfに制限されているわけではなさそうです。

管理用の別ネットワークがあったときに、経路が混ざらない、というだけのようです。

装置への通信はCoPPとコントロールプレーンACLで制御できます。

処理の順序は、CoPP → コントロールプレーンACL、の順になっています。

<br><br>

## logging設定

まだ調べてないのでよくわからないのですが、装置の/var/log/に吐き出されてるのかな？

これから調べます。

`show log`　/var/log配下にあるファイルを表示

arcosディレクトリにログがある

`monitor start`　リアルタイムにログを表示、tail -fと同等





## debug

特定のプロトコルはデバッグをきめ細かく指定できる。

`tech-support bgp-debug neighbor address 2001:db8:ffff::2 op on`

それ以外は汎用のdebugコマンドを使う。

`debug acl enable all`

何がデバッグ対象になっているかは、`show debug`で確認する。

有効にすると /var/log/arcos/<protocol>.bin_logfile.txt に記録される。

`monitor start` でそのファイルを指定すればリアルタイムに表示。

ログファイルは10MBを超えるとローテートする。

debugは必ず止めること。


<br><br>

## NTP設定

まだ調べてません。

タイムゾーンはAsia/Tokyoに変更できましたが、NTPの設定は分かりません。

もしかして、Linux本体で時刻同期するのかな？

<br><br>

## SNMP設定

制限のかけ方を中心に調べる予定。


<br><br>

## 調べること

キャプチャしてデフォルト状態で流れるパケットを確認する

maインタフェースではDHCPv6パケットが送信され続けるので、これを停止したい。

LLDPも停止したい。

他にないかな？


ポートスキャンをかけてみて、どのポートが開いているかを確認したい。

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