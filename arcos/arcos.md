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

別のルータからrootでSSH接続した場合の例。普通に入れてしまいます。

```bash
root@PE14# ssh 2001:db8:ffff::1
The authenticity of host '2001:db8:ffff::1 (2001:db8:ffff::1)' can't be established.
ED25519 key fingerprint is SHA256:j0trpa9kntLW6sgyGNQynA7tnfRnY5kjFoJe80uf34I.
This key is not known by any other names.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '2001:db8:ffff::1' (ED25519) to the list of known hosts.
ArcOS (c) Arrcus, Inc.
root@2001:db8:ffff::1's password:
root@P1:~#
root@P1:~#
```

SSH接続をmanagement vrfに制限する方法はなさそうです。

商用環境だとインバンドでの接続が解放されているとまずいので、装置へのアクセス制御をしっかりとかけなければいけません。

<br><br>

## 設定関連の操作

コンフィグモードに入る方法

```bash
root@P1# conf ?
Possible completions:
  exclusive   Obtain an exclusive lock on the candidate database
  shared      Work in a shared candidate database
  terminal    Work in a private candidate database (default)
  |           Output modifiers
  <cr>
```

コンフィグモードの抜け方

**exit** 編集中のコンフィグがなければオペレーションモードに戻ります

**end** 編集中のコンフィグがなければオペレーションモードに戻ります

**ctrl-z** 編集中のコンフィグがなければオペレーションモードに戻ります

**abort** 編集中のコンフィグがあっても、それを破棄して抜けます

編集中のコンフィグがあるときは、次のように動作を促されます。

```bash
root@P1(config)# exit
Uncommitted changes found, commit them? [yes/no/CANCEL]
```

変更した設定はcommitで反映します。

```bash
oot@P1(config)# commit ?
Possible completions:
  comment        Add a commit comment
  label          Add a commit label
  persist-id     Specify a persist-id
  rollback-id    Display rollback-id for commit
  save-running   Save running to file before performing the commit
  ---
  abort          Abort a pending commit
  and-quit       Commit current set of changes and exit configuration mode
  check          Validate current configuration
  confirmed      Commit current set of changes with a timeout
  no-confirm     Commit current set of changes, do not query user
  <cr>
```

ラベルとコメントを付けてコミットしてみます。
コメントに空白を含む場合はダブルクオートで囲みます。

```bash
root@P1(config)# commit label LABEL-1 comment "change hostname by iida"
```

過去のコミット履歴を確認するには　`show configuration commit list`　です。

```bash
root@PP1# show configuration commit list
2025-12-16 13:57:31
SNo. ID       User       Client      Time Stamp          Label       Comment
~~~~ ~~       ~~~~       ~~~~~~      ~~~~~~~~~~          ~~~~~       ~~~~~~~
0    10101    root       cli         2025-12-16 13:55:55 LABEL-1     change hostname by iida
1    10100    root       cli         2025-12-16 09:46:19
2    10099    root       cli         2025-12-16 09:42:35
```

上が新しいです。シリアル番号は最新が0です。

そのコミットで何を変更したのかを確認するには　`show configuration commit changes ＜番号＞`　です。

```bash
root@PP1# show configuration commit changes 0
!
! Created by: root
! Date: 2025-12-16 13:55:55
! Client: cli
! Label: LABEL-1
! Comment: change hostname by iida
!
system hostname PP1
```

過去のコミットに戻すこともできますが、これは設定変更になるのでコンフィグモードに移らないとできません。

コンフィグモードで　`rollback configuration ＜番号＞`　です。

一つ前の状態、すなわち番号1に戻してみます。

```bash
root@PP1(config)# rollback configuration ?
Possible completions:
  0      2025-12-16 13:55:55 by root via cli label LABEL-1 comment change
         hostname by iida
  1      2025-12-16 09:46:19 by root via cli

root@PP1(config)# rollback configuration 1
root@PP1(config)#
```

この時点では何も起きてないように見えますが、変更はcandidate-configの中に反映されてます。

```bash
root@PP1(config)# show configuration
system hostname P1
root@PP1(config)#
```

改めてコミットすれば反映されます。

<br>

コミットしてから一定時間経過したら自動でもとに戻すこともできます。

排他コンフィグモードで　`commit confirmed ＜分＞`　です。

排他コンフィグモードではない、通常のコンフィグモードで実際にやってみると、次のようなエラーになります。

```bash
root@PP1(config)# commit confirmed ?
Possible completions:
  <timeout>   Number of minutes until rollback <1..65535>
  <cr>
root@PP1(config)# commit confirmed 10
Error: confirmed commit is not supported in 'private' mode
root@PP1(config)#
```

排他コンフィグモードでやってみます。

```bash
root@PP1# config exclusive
Entering configuration mode exclusive
Warning: uncommitted changes will be discarded on exit
root@PP1(config)#
root@PP1(config)# rollback configuration 1
root@PP1(config)# commit confirmed 1
root@PP1(config)# rollback configuration 1
root@PP1(config)# commit confirmed 1
Warning: The configuration will be reverted if you exit the CLI without
performing the commit operation within 1 minutes.
root@P1(config)#
```

設定が反映されたのでプロンプトが PP1 から P1 に戻ってます。

１分経過すると、

```bash
root@P1(config)#
Message from system at 2025-12-16 14:11:25...
confirmed commit operation not confirmed by root from cli
configuration rolled back
root@P1(config)#
root@PP1(config)#
root@PP1(config)#
```

元の設定に戻ります。

指定した時間内に、確定するには commit を再度実行します。

```bash
root@PP1(config)# rollback configuration 1
root@PP1(config)# commit confirmed 1
Warning: The configuration will be reverted if you exit the CLI without
performing the commit operation within 1 minutes.
root@P1(config)#
root@P1(config)# commit
Commit complete. Configuration is now permanent.
root@P1(config)#
```

タイムアウトを待たずとも、不都合が発覚したらすぐさま取り消すこともできます。

```bash
root@PP1(config)# rollback configuration 1
root@PP1(config)# commit confirmed 1
Warning: The configuration will be reverted if you exit the CLI without
performing the commit operation within 1 minutes.
root@P1(config)#
root@P1(config)#
root@P1(config)#
root@P1(config)# commit abort
Confirmed commit has been aborted. Old configuration will now be restored.
root@PP1(config)#
Message from system at 2025-12-16 14:14:39...
confirmed commit operation not confirmed by root from cli
configuration rolled back
root@PP1(config)#
root@PP1(config)#
```

ホスト名が PP1 だったのが、ロールバックして P1 に戻りましたが、abortしたので元の PP1 に戻ってます

<br>

装置のコンフィグをLinux上のファイルとして保存できます。

```text
root@PP1# show running-config | save config.txt
```

rootの場合はexitでCLIを抜けてbashに戻るかと、保存したファイルを確認できます。

```bash
root@P1:~# ls
config.txt
root@P1:~#
```

bashに戻らずとも、CLIの中からも確認できます。

```bash
root@PP1# file list
.bash_history
.bashrc
.config
.lesshst
.lttngrc
.profile
.ssh
config.txt
root@PP1#
```

<br>

保存しておいたファイルからロードすることもできます。

**merge** - 現在の設定にファイルの中身をマージします

**override** - 今動いている設定を全て消してから、ファイルの中身を反映させます

**replace** - ファイルの内容で置き換え、ファイルにない部分は今のコンフィグを継続します

この3個はNETCONFで定義されているものと同じと考えられます。

mergeとreplaceは近しい動作で分かりづらいです。

mergeの場合、新しい設定にのみ存在する要素は追加され、両方に存在する要素は新しい値で更新、既存の設定にのみ存在する要素は変更されず、削除もされません。

replaceの場合、既存の設定データを新しい設定データで完全に置き換えます。もし既存の設定に存在する要素が新しい設定データに含まれていなければ、それらの要素は削除されます。

overrideは初期化した状態からの回復になるので、丸ごと入れ替えるときに使います。

全文を含むコンフィグの場合、どれを選んでも変わらないので、試しにここでは `system hostname PP1` という１行だけを含んだファイルを作って、それをロードしてみます。

まずは **merge** の場合。期待通りの動きをします。

```bash
root@P1# config
Entering configuration mode terminal
root@P1(config)# load merge config.txt
Loading.
20 bytes parsed in 0.02 sec (961 bytes/sec)
root@P1(config)# show config
system hostname PP1
root@P1(config)# commit
Commit complete.
root@PP1(config)#
```

次に **override** の場合。

部分的なコンフィグしかないのにoverrideするのは超危険な操作です。

ファイルに書いてあるのが `system hostname PP1` だけなので、
それ以外の部分は全部noで消してデフォルトに戻そうとします。

show configで何が変更されるのかを確認して、おかしいことに気づけばabortで抜けるだけです。

```bash
oot@P1(config)# load override config.txt
Loading.
20 bytes parsed in 0.15 sec (131 bytes/sec)
root@P1(config)#
root@P1(config)# show configuration
system hostname PP1
no version "8.3.1.EFT1:Nov_20_25:6_11_PM [release] 2025-11-20 18:11:22"
no features feature ARCOS_RIOT
no features feature ARCOS_ICMP_SRC_REWRITE
no features feature ARCOS_SUBIF
no features feature ARCOS_QoS
no features feature ARCOS_MPLS
no features feature ARCOS_SFLOW
no system login-banner "ArcOS (c) Arrcus, Inc."
no system clock timezone-name Asia/Tokyo
no system ssh-server enable true
no system ssh-server permit-root-login true
```

最後に **replace** の場合です。投入されているのが1行だけだとmergeと区別が付きません。

```bash
root@P1(config)# load replace config.txt
Loading.
20 bytes parsed in 0.02 sec (932 bytes/sec)
root@P1(config)# show config
system hostname PP1
root@P1(config)#
```

コンフィグをツリーの階層構造で考えたときに、そのツリーを丸ごと入れ替えるのがreplace、指定されたものだけを入れ替えて既に存在している部分は残すのがmergeです。

<br><br><br>

# L3VPN over SRv6

<br>

いろいろ検証するための環境として L3VPN over SRv6 を構築します。

個人的に、この環境を簡単に作れると **良い装置** という印象を持ちます。

ArcOSはとても簡単だったので、良い装置です。

<br>

![構成](/assets/arcos_l3vpn.png)

<br>

このラボはPythonスクリプトで作成しますが、手順を踏む必要があるため `make` コマンドを使います。

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

## 装置の管理アドレス

ループバックにIPv4とIPv6アドレスを割り当てて、それを装置を代表するアドレスにします。

ICMPメッセージの送信元IPアドレスは指定するようにします。

```text
!
system icmp source-interface loopback0
 network-instance default
!
```

<br><br>

## 装置へのアクセス制御

初期状態でmanagementという名前のvrfが作られています。

SNMPやSSH、NETCONF、RESTCONF等の管理通信がmanagement vrfに限定されている、ということはないようです。

装置自身への着信通信は別途制限を付ける必要があります。

これはCoPPとコントロールプレーンACLで制御します。

処理の順序は、CoPP → コントロールプレーンACL、の順になっています。

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

Capabilityを確認する例。

`./nc.py capability`

```bash
cisco@jumphost:~/expt-cml/arcos$ ./nc.py capability
➡️ NETCONF接続を試行中: 192.168.254.1:830 (ユーザー: cisco)
✅ NETCONFセッションが確立されました。セッションID: 191

📋 サーバのCapabilities一覧 (128件):

================================================================================

[YANG Modules] (112件)
  - INET-ADDRESS-MIB
  - IPV6-TC
  - SNMPv2-SMI
  - SNMPv2-TC
  - TRANSPORT-ADDRESS-MIB
  - arcos-chassis
  - arcos-ldp-debug
  - arcos-rsvp-debug-mplste
  - arcos-rsvp-debug-proto
  - confd_dyncfg
  ... and 102 more modules
  (--verbose オプションで全て表示)

[Operations]
  urn:ietf:params:netconf:capability:confirmed-commit:1.1
  urn:ietf:params:netconf:capability:confirmed-commit:1.0
  urn:ietf:params:netconf:capability:candidate:1.0
  urn:ietf:params:netconf:capability:rollback-on-error:1.0
  urn:ietf:params:netconf:capability:url:1.0?scheme=ftp,sftp,file
  urn:ietf:params:netconf:capability:validate:1.0
  urn:ietf:params:netconf:capability:validate:1.1
  urn:ietf:params:netconf:capability:xpath:1.0
  urn:ietf:params:netconf:capability:notification:1.0
  urn:ietf:params:netconf:capability:partial-lock:1.0
  urn:ietf:params:netconf:capability:with-defaults:1.0?basic-mode=explicit&also-supported=report-all-tagged,report-all
  urn:ietf:params:netconf:capability:with-operational-defaults:1.0?basic-mode=explicit&also-supported=report-all-tagged,report-all
  urn:ietf:params:netconf:capability:yang-library:1.0?revision=2019-01-04&module-set-id=a16375f5c78e8d07ffef0c170609ef94
  urn:ietf:params:netconf:capability:yang-library:1.1?revision=2019-01-04&content-id=a16375f5c78e8d07ffef0c170609ef94

================================================================================

接続を閉じました。
```

<br>

XML形式の設定を取得してファイルに保存する例。

`./nc.py get`

```bash
cisco@jumphost:~/expt-cml/arcos$ ./nc.py get
➡️ NETCONF接続を試行中: 192.168.254.1:830 (ユーザー: cisco)
✅ NETCONFセッションが確立されました。セッションID: 61

➡️ <get-config> RPCを送信中 (ソース: <running>)...
✅ XMLパースが完了しました。ルート要素: {urn:ietf:params:xml:ns:netconf:base:1.0}rpc-reply
✅ XMLパースが完了しました。ルート要素: {urn:ietf:params:xml:ns:netconf:base:1.0}rpc-reply
✅ XML設定を保存しました: /tmp/192.168.254.1.xml
```

<br>

/tmp/192.168.254.1.xml に保存されたので、これを手動で編集して、ホスト名を変更します。

手動で変更したXML形式のファイルを適用する例。

`./nc.py apply -f /tmp/192.168.254.1.xml`

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

<br>

実行すると、ルータのコンソールには次のように表示されます。

```text
root@P1#
System message at 2025-12-15 16:08:40...
Commit performed by cisco via ssh using netconf.
root@P1#
root@PP1#
```

自動でコミットされました。

ホスト名が変更されたことでプロンプトも変化しています。

<br>

一定時間後に元の設定に戻す場合（confirmed commit）

`./nc.py apply-confirmed -f /tmp/192.168.254.1.xml`

```bash
cisco@jumphost:~/expt-cml/arcos$ ./nc.py apply-confirmed -f /tmp/192.168.254.1.xml
➡️ NETCONF接続を試行中: 192.168.254.1:830 (ユーザー: cisco)
✅ NETCONFセッションが確立されました。セッションID: 238

➡️ <edit-config> RPCを送信中...
   設定ファイル: /tmp/192.168.254.1.xml
✅ <edit-config>が成功しました (target=candidate)

➡️ <commit confirmed> RPCを送信中 (timeout: 120秒)...
   persist ID: nc.py
✅ <commit confirmed>が成功しました。

⚠️ 設定は一時的に適用されました。120秒以内に以下のコマンドで変更を永続化してください:
   python nc.py confirm --persist-id nc.py

   時間内に確定コミットが行われない場合、変更は自動的にロールバックされます。
   手動でロールバックするには以下のコマンドを実行してください:
   python nc.py cancel --persist-id nc.py

接続を閉じました。
```
<br>

このときルータのコンソールには以下のように表示されます。設定変更でホスト名がP1からPP1に変わっています。

```text
System message at 2025-12-16 07:42:55...
Commit performed by cisco via ssh using netconf.
root@P1#
root@PP1#
```

<br>

そのまま放置すると、2分後にルータのコンソールにメッセージが表示されて、設定はもとに戻ります。

```bash
root@PP1#
Message from system at 2025-12-16 07:44:55...
confirmed commit operation not confirmed by cisco from netconf
configuration rolled back
root@PP1#
root@P1#
root@P1#
```

<br>

2分以内に確定すれば永続化できます。

```bash
cisco@jumphost:~/expt-cml/arcos$ ./nc.py confirm
➡️ NETCONF接続を試行中: 192.168.254.1:830 (ユーザー: cisco)
✅ NETCONFセッションが確立されました。セッションID: 331

➡️ 設定変更を確定するため <commit> RPC を送信中...
✅ <commit>が成功しました。保留中の変更が永続化されました。

接続を閉じました。
```

<br>

2分待たずにキャンセルすることもできます。

```bash
cisco@jumphost:~/expt-cml/arcos$ ./nc.py cancel
➡️ NETCONF接続を試行中: 192.168.254.1:830 (ユーザー: cisco)
✅ NETCONFセッションが確立されました。セッションID: 338

➡️ 設定変更をキャンセルするため <cancel-commit> RPC を送信中...
✅ <cancel-commit>が成功しました。保留中の変更はロールバックされました。

接続を閉じました。
```

<br>

ルータのコンソールにはこのようなメッセージが表示されます。

```text
Message from system at 2025-12-16 08:38:24...
confirmed commit operation not confirmed by cisco from netconf
configuration rolled back
root@P1#
```

<br><br>

## RESTCONF

RFC8040

HTTPSを使うRESTCONFはTCPポート8009です。

暗号化されないHTTPのRESTCONFはTCPポート8008です。

`system restconf-server enable true`

この設定でどのポートが開く？

```
root@P1(config)# system restconf-server transport-security ?
Description: Configure RESTCONF transport security
Possible completions:
  [true]
  false
  true
```

```
root@P1(config)# system restconf-server listen-addresses ?
Description: Listen IP addresses for the RESTCONF server
Possible completions:
  <address>   IPv4 or IPv6 address
  ANY         Listen on all IP addresses (IPv4/IPv6)
  [
```


```bash
curl -k -u cisco:cisco123 \
-H "Content-Type: application/yang-data+json" \
-H "Accept: application/yang-data+json" \
-i https://192.168.254.1:8009/<URI>
```


GET /restconf/data
GET /restconf/data/openconfig-interfaces:interfaces
GET /restconf/data/openconfig-interfaces:interfaces
GET /restconf/data/openconfig-interfaces:interfaces/interface=Ethernet0%2F0

%2Fはスラッシュ/

GET /restconf/data/openconfig-interfaces:interfaces/interface=Ethernet0%2F0/config
GET /restconf/data/openconfig-interfaces:interfaces/interface=Ethernet0%2F0/state
GET /restconf/data/openconfig-interfaces:interfaces/interface=Ethernet0%2F0/state/counters

GET /restconf/data/openconfig-system:system
GET /restconf/data/openconfig-system:system/config/hostname
GET /restconf/data/openconfig-system:system/ntp/config/enabled


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

ターゲットが単一ルータの場合は、同期処理で実装するのが簡単です。

サンプルスクリプト　[gnmi.py](/arcos/gnmi.py)

実行例。

```bash
cisco@jumphost:~/expt-cml/arcos$ ./gnmi.py
✅ ルータ 192.168.254.1:9339 への接続に成功しました。

⏳ Subscribe (mode=STREAM) リクエストを送信中... (Ctrl+Cで終了)
時刻: 1765796248495984113, パス: interfaces/interface[name=swp1]/state/counters/in-octets, 値: 12384867
時刻: 1765796248496053115, パス: interfaces/interface[name=swp1]/state/counters/out-octets, 値: 12394757
時刻: 1765796278518973062, パス: interfaces/interface[name=swp1]/state/counters/out-octets, 値: 12403869
時刻: 1765796278519134420, パス: interfaces/interface[name=swp1]/state/counters/in-octets, 値: 12393980
時刻: 1765796308514761891, パス: interfaces/interface[name=swp1]/state/counters/out-octets, 値: 12416160
時刻: 1765796308514860266, パス: interfaces/interface[name=swp1]/state/counters/in-octets, 値: 12403284
✅ プログラムを終了します。
```

ターゲットが複数のルータの場合、同時にコネクションを張り続けることになりますので、非同期の方が望ましいです。

サンプルスクリプト　[gnmi_async.py](/arcos/gnmi_async.py)








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