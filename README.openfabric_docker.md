# FRR(Docker)でOpenFabricを検証する

CML2.9以降でDockerイメージが動作するようになっています。

CML2.9に含まれるFRR(Docker)のバージョンは `FRRouting 10.2.1` です。
このイメージでOpenFabricの動作を試したところ、期待通りには動きませんでした。

そこで新しいバージョンのFRRイメージを作成して試します。
Dockerイメージの作り方は後述します。

<br>

## ラボ構成

スクリプト `bin/cml_create_openfabric_docker_lab.py` を使ってCML内にラボを自動生成します。

<br>

![ラボ構成](/assets/openfabric_docker_lab.png)

<br>

## R1のルーティングテーブル

IPv4のルーティングテーブル。期待通りです。

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

R1からR8へのping

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

R1からR13へのping

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

IPv6のルーティングテーブル。これも期待通りです。

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

R1からR8へのping

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

R1からR13へのping

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

ルータ・ルータ間にはIPv6リンクローカルアドレスしか設定していませんが、IPv4およびIPv6ともに疎通できています。

<br>

> [!NOTE]
>
> FRRメモ
>
> - hostnameコマンドで名前を付けても、それは現在接続しているvtyshにしか反映されません。writeしても、どこにも保存されません。

<br><br><br>

# FRRのDockerイメージの作り方

少々手間はかかりますが、自分で作ったDockerイメージをCMLで動かすこともできます。

<br>

> [!NOTE]
>
> AlpineをベースにしてFRR 10.4をソースコードからビルドしてみましたが、それも挙動不審でした。
>
> サイズは大きくなってしまいますが、Ubuntu24をベースにFRRのDockerイメージを作成します。

<br>

## 母艦の設定

コックピットにログインしてターミナルを開きます。

root特権を取ります。

```bash
sudo -s -E
```

`/etc/sysctl.conf` を編集します。

```bash
vi /etc/sysctl.conf
```

この部分のコメントを外します。

```text
# Uncomment the next line to enable packet forwarding for IPv4
net.ipv4.ip_forward=1

# Uncomment the next line to enable packet forwarding for IPv6
#  Enabling this option disables Stateless Address Autoconfiguration
#  based on Router Advertisements for this host
net.ipv6.conf.all.forwarding=1
```

再起動します。

```bash
reboot
```

> [!NOTE]
>
> dockerdは起動時にホストがIPv6中継可能かどうかをチェックしていますので、`sysctl -p` で反映させただけではだめです。
> CMLそのものを再起動したほうが早いです。

<br>

## DockerをインストールしたUbuntuを用意する

CML上にラボを作成してUbuntuと外部接続を用意します。

そのくらい簡単なラボは手作業で作ってもよいのですが、このスクリプトを実行すれば自動で作成できます。

```bash
bin/cml_create_lab1.py
```

このスクリプトを再度実行すると同じ名前のものは消えてしまいますので、
間違って消さないようにラボの名前を適当に変えておきます。

UbuntuにDockerのインストールが必要ですので、事前準備として必要なツールをインストールします。

Ubuntuにログインします。

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg
```

aptリポジトリを追加します。

```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
```

dockerグループを作成してciscoアカウントをグループに所属させます（デフォルトのアカウントがciscoの場合）。

```bash
sudo groupadd docker
sudo usermod -aG docker cisco
```

docker-engineをインストールします。

```bash
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Ubuntuを再起動します。

```bash
sudo reboot
```

これら一連の動作はcloud-initの中でやった方がよかったかもしれません。

<br>

> [!NOTE]
>
> dockerコマンド早見表
>
> - `docker ps -a`　止まっているものを含めてプロセスを確認
> - `docker stop`　停止
> - `docker rm`　削除
> - `docker image ls`　存在するイメージの確認
> - `docker rmi`　イメージを削除
> - `docker system prune --all`　キャッシュの削除、再ビルドする前に実行
> - `docker tag IMAGE_ID IMAGE_NAME:TAG`　作成済みイメージの名前とタグを変更
> - `docker exec -it ID bash`　シェルを起動

<br>

## FRRのDockerイメージをビルドします

Ubuntuを再起動したら再度ログインします。

このリポジトリの `frr` ディレクトリに Dockerfile と Makefile を作成したのでそれを利用してFRRのイメージを作っていきます。

Makefileはこのようになっていますので、これを見ながらdockerコマンドを叩いても結果は同じです。

```bash
.DEFAULT_GOAL := help
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

TAG ?= frr:10.5-iida

build: ## Dockerイメージを作成する
	@docker build -t ${TAG} -f Dockerfile .


inspect: ## DockerイメージのIDをインスペクトする
	@docker inspect ${TAG} | grep -i sha256 | head -n 1 | awk '{print $$2}'


save: ## Dockerイメージを保存する
	@docker save -o frr.tar ${TAG}
	@gzip frr.tar


run: ## Dockerコンテナを起動する
	@docker run -d --rm --init --privileged --name frr-iida ${TAG}


shell: ## Dockerコンテナにシェルで入る
	@docker exec -it frr-iida bash


stop: ## Dockerコンテナを停止する
	@docker stop frr-iida


clean: ## Dockerイメージを削除する
	@docker rmi $$(docker images -q)
	@rm -f frr.tar.gz
```

リポジトリをクローンします。

```bash
git clone https://github.com/takamitsu-iida/expt-cml.git
```

移動します。

```bash
cd expt-cml
cd frr
```

ラクをするためにmakeを使いたいのでインストールします。

```bash
sudo apt install -y make
```

繰り返しdockerイメージを作るときにはキャッシュが悪さをするかもしれませんので削除します（dockerインストール直後の場合は省略して構いません）。

```bash
docker system prune --all
```

Dockerfileの内容に従ってビルドします。長い時間かかります。10分以上かかります。

```bash
make build
```

作成したdockerイメージをインスペクトしてIdの値を調べます。

実行例。

```bash
make inspect
```

実行例。

```bash
root@ubuntu-0:~/expt-cml/frr# make inspect
"sha256:dcb26c9c1ba66cdb17c6d3b7e2d1952abffd96b832a855ad4dd7e4c559a76d71",
```

sha256に続く値がIdの値です。このあと使いますのでどこかにメモしておきます。

イメージをtar形式で保存します。

```bash
make save
```

ファイルfrr.tar.gzが生成されます。

このfrr.tar.gzをscpでCMLにアップロードします。
アップロード先のディレクトリは指定できません。`dropfolder` という特別な場所に保存されます。

<br>

> [!NOTE]
>
> dropfolderの実体は `/var/local/virl2/dropfolder` です。

<br>

この転送はびっくりするくらい高速です。

```bash
scp frr.tar.gz admin@192.168.122.212:
```

ここからはコックピットのターミナルに移ります（Webブラウザのターミナルよりも、SSHで接続した方が快適です）。

ルート特権を取ります。

```bash
sudo -s -E
```

ノード定義ファイルの格納場所に移動します。

```bash
cd /var/lib/libvirt/images/node-definitions
```

ノード定義ファイルを新規で作ります。

```bash
vi frr-10-5-iida.yaml
```

もしくは元になっているfrr.yamlをコピーします。

```bash
cp -a frr.yaml frr-10-5-iida.yaml
```

[frr/cml_node_definition.yaml](/frr/cml_node_definition.yaml) の内容をコピペして保存します。

ファイルのオーナーを変更します。

```bash
chown libvirt-qemu:virl2 frr-10-5-iida.yaml
```

<br>

> [!NOTE]
>
> githubにあるものをcurlで取ってきたほうが速いかもしれません。
>
> ```bash
> curl -H 'Cache-Control: no-cache' -Ls https://raw.githubusercontent.com/takamitsu-iida/expt-cml/refs/heads/master/frr/cml_node_definition.yaml --output frr-10-5-iida.yaml
>
> chown libvirt-qemu:virl2 frr-10-5-iida.yaml
> ```

<br>

> [!NOTE]
>
> ノード定義ファイルはCML2.9に同梱のFRRのそれを元にして加工しています。
> FRRの中でwriteして保存した設定が恒久的に残るように、以下のようにマウント設定を変えています。
> この設定にすると/etc/frr/frr.conf.savを作れずにエラーを吐きますが無視して構いません。
>
> ```json
> "mounts": [
>   "type=bind,source=cfg/boot.sh,target=/config/boot.sh",
>   "type=bind,source=cfg/node.cfg,target=/etc/frr/frr.conf",
>   "type=bind,source=cfg/protocols,target=/config/protocols"
> ],
> ```

<br>

次にイメージ定義を作ります。

イメージ定義が置かれている場所に移動します。

```bash
cd /var/lib/libvirt/images/virl-base-images
```

ディレクトリを作ります。

```bash
mkdir frr-10-5-iida
chown libvirt-qemu:virl2 frr-10-5-iida
```

移動します。

```bash
cd frr-10-5-iida
```

コックピット側のdropfolderからファイルを移動します。

```bash
mv /var/local/virl2/dropfolder/frr.tar.gz .
chown libvirt-qemu:virl2 frr.tar.gz
```

イメージ定義ファイルを作成します。

```bash
vi frr-10-5-iida.yaml
```

[frr/cml_image_definition.yaml](/frr/cml_image_definition.yaml) の内容をコピペします。

内容はこのようになっています。

```yaml
#
# Free Range Routing image definition
# generated 2025-08-15
# part of VIRL^2
#

id: frr-10-5-iida
label: Free Range Routing (frr) 10.5-iida
description: Free Range Routing (frr) 10.5-iida (Docker)
node_definition_id: frr-10-5-iida
disk_image: frr.tar.gz
read_only: true
schema_version: 0.0.1
sha256:
```

<br>

> [!NOTE]
>
> イメージ定義ファイルもgithubから採取した方が簡単かもしれません。
>
> ```bash
> curl -H 'Cache-Control: no-cache' -Ls https://raw.githubusercontent.com/takamitsu-iida/expt-cml/refs/heads/master/frr/cml_image_definition_alpine.yaml --output frr-10-5-iida.yaml
>
> chown libvirt-qemu:virl2 frr-10-4-iida.yaml
> ```

<br>

sha256の部分をイメージをインスペクトしたときにメモしたものに置き換えます。

virl2を再起動します。

```
systemctl restart virl2.target
```

dockerのイメージを確認します。

```bash
root@cml-controller:/var/lib/libvirt/images/virl-base-images/frr-10-5-iida# docker images
REPOSITORY   TAG         IMAGE ID       CREATED        SIZE
frr          10.2.1-r1   1bd2e82159f1   4 months ago   39.8MB
```

この時点では登録されていません。

CMLのダッシュボードに移ります。

FRR-10-5-iidaをドラッグしてイメージを一つ作ってみます。

STARTで起動します。

コックピットでdockerのイメージを確認します。

```bash
root@cml-controller:/var/lib/libvirt/images/virl-base-images/frr-10-5-iida# docker images
REPOSITORY   TAG         IMAGE ID       CREATED         SIZE
frr          10.5-iida   dcb26c9c1ba6   8 minutes ago   1.06GB
frr          10.2.1-r1   1bd2e82159f1   4 months ago    39.8MB
```

イメージが一つ、増えました。

> [!NOTE]
>
> ラボでイメージをドラッグドロップした時点では何も起きていません。
> `/usr/local/virl2/images/{{ラボのUUID}}` に実体化されたイメージが格納されますが、ドラッグドロップしただけでは作られません。
> STARTで起動して初めてイメージが実体化されます。


<br><br><br><br><br><br>

# 【参考】CML2.9のDockerの挙動を調査してみる

CMLで適当なラボを作って、CML2.9に同梱されているFRRをインスタンス化して起動してみます。

コックピットのターミナルでイメージの置かれているディレクトリを確認すると、いくつかファイルが作られています。

```bash
root@cml-controller:/var/local/virl2/images/5ae0eb2d-ec7f-4ef4-a610-1a22f854cd11/894b8a48-3a9f-46d9-bf9f-c3d649dac49c/cfg# ls -l
total 16
-rw-r--r-- 1 virl2 virl2  99 Aug 15 06:44 boot.sh
-rw-r--r-- 1 virl2 virl2 734 Aug 15 06:44 config.json
-rw-r--r-- 1 virl2 virl2 665 Aug 15 06:44 node.cfg
-rw-r--r-- 1 virl2 virl2 249 Aug 15 06:44 protocols
```

`boot.sh`　と　`node.cfg`　と　`protocols`　はCMLのウェブ画面で指定する設定ファイルです。

`config.json`　はdockerの設定ファイルのようで、中身はこんな感じになっています。

```bash
root@cml-controller:/var/local/virl2/images/5ae0eb2d-ec7f-4ef4-a610-1a22f854cd11/894b8a48-3a9f-46d9-bf9f-c3d649dac49c/cfg# cat config.json
{
  "docker": {
    "image": "frr:10.2.1-r1",
    "mounts": [
      "type=bind,source=cfg/boot.sh,target=/config/boot.sh",
      "type=bind,source=cfg/node.cfg,target=/config/node.cfg",
      "type=bind,source=cfg/protocols,target=/config/protocols"
    ],
    "caps": [
      "CAP_CHOWN",
      "CAP_DAC_OVERRIDE",
      "CAP_FOWNER",
      "CAP_FSETID",
      "CAP_KILL",
      "CAP_MKNOD",
      "CAP_NET_BIND_SERVICE",
      "CAP_NET_RAW",
      "CAP_SETFCAP",
      "CAP_SETGID",
      "CAP_SETPCAP",
      "CAP_SETUID",
      "CAP_SYS_CHROOT",
      "NET_ADMIN",
      "SYS_ADMIN"
    ],
    "env": [
      "MAX_FDS=100000"
    ]
  },
  "shell": "/bin/bash",
  "day0cmd": [ "/bin/bash", "/config/boot.sh" ],
  "busybox": true
}
```

<br>

ラボ内にイメージを作成するたびにこれらファイルが作られるということは、
どこかでこれらファイルを作成するように指示してはずです。それはどこでしょう？

ノード定義ファイルを覗いてみます。

```bash
root@cml-controller:/var/lib/libvirt/images/node-definitions# cat frr.yaml
#
# Free Range Routing node definition
# generated 2025-05-27
# part of VIRL^2
#

id: frr
configuration:
  generator:
    driver: iosv
  provisioning:
    volume_name: cfg
    media_type: raw
    files:
      - name: config.json
        editable: false
        content: |
          {
            "docker": {
              "image": "frr:10.2.1-r1",
              "mounts": [
                "type=bind,source=cfg/boot.sh,target=/config/boot.sh",
                "type=bind,source=cfg/node.cfg,target=/config/node.cfg",
                "type=bind,source=cfg/protocols,target=/config/protocols"
              ],
              "caps": [
                "CAP_CHOWN",
                "CAP_DAC_OVERRIDE",
                "CAP_FOWNER",
                "CAP_FSETID",
                "CAP_KILL",
                "CAP_MKNOD",
                "CAP_NET_BIND_SERVICE",
                "CAP_NET_RAW",
                "CAP_SETFCAP",
                "CAP_SETGID",
                "CAP_SETPCAP",
                "CAP_SETUID",
                "CAP_SYS_CHROOT",
                "NET_ADMIN",
                "SYS_ADMIN"
              ],
              "env": [
                "MAX_FDS=100000"
              ]
            },
            "shell": "/bin/bash",
            "day0cmd": [ "/bin/bash", "/config/boot.sh" ],
            "busybox": true
          }
      - name: node.cfg
        editable: true
        content: |
          ! FRR Config generated on 2025-01-22 17:55
          ! just an example -- You need to need to change it
          !
          hostname frr-0
          !
          interface lo
              ip address 10.0.0.1/32
              ip ospf passive
          !
          interface eth0
              description to eth0.frr-1
              ip address 172.16.128.2/30
              no shutdown
          interface eth1
              description to eth0.frr-2
              ip address 172.16.128.9/30
              no shutdown
          interface eth2
              description not connected
              !no ip address
              shutdown
          interface eth3
              description not connected
              !no ip address
              shutdown
          !
          router ospf
              ospf router-id 10.0.0.1
              network 10.0.0.1/32 area 10
              network 172.16.128.0/30 area 10
              network 172.16.128.8/30 area 10
          !
          end
      - name: boot.sh
        editable: true
        content: |
          # insert more commands here
          # ip address add dev eth1 10.0.0.1/24
          # ip link set dev eth1 up
          exit 0
      - name: protocols
        editable: true
        content: |
          # enable / disable needed routing protocols by adding / removing
          # the hashmark in front of the lines below
          #
          # bgpd
          ospfd
          # ospf6d
          # ripd
          ripngd
          # isisd
          # pimd
          # pim6d
          # ldpd
          # nhrpd
          eigrpd
          # babeld
          # sharpd
          # pbrd
          # bfdd
          # fabricd
          # vrrpd
          # pathd
device:
  interfaces:
    has_loopback_zero: false
    min_count: 1
    default_count: 4
    management:
      - eth0
    physical:
      - eth0
      - eth1
      - eth2
      - eth3
      - eth4
      - eth5
      - eth6
      - eth7
      - eth8
      - eth9
      - eth10
      - eth11
      - eth12
      - eth13
      - eth14
      - eth15
      - eth16
      - eth17
      - eth18
      - eth19
      - eth20
      - eth21
      - eth22
      - eth23
      - eth24
      - eth25
      - eth26
      - eth27
      - eth28
      - eth29
      - eth30
      - eth31
    serial_ports: 2
inherited:
  image:
    ram: true
    cpus: true
    cpu_limit: true
    data_volume: false
    boot_disk_size: false
  node:
    ram: true
    cpus: true
    cpu_limit: true
    data_volume: false
    boot_disk_size: false
general:
  description: Free Range Routing (Docker)
  nature: router
  read_only: true
schema_version: 0.0.1
sim:
  linux_native:
    cpus: 1
    ram: 256
    driver: server
    libvirt_domain_driver: docker
    cpu_limit: 100
boot:
  timeout: 30
  completed:
    - READY
pyats:
  os: ios
  series: iosv
  config_extract_command: show run
ui:
  description: |
    Free Range Routing (frr) 10.2.1-r1
  group: Others
  icon: router
  label: FRR
  label_prefix: frr-
  visible: true
```

なるほど、疑問解消です。先ほど確認したファイルの内容がノード定義ファイルの中に書かれてます。

ラボ内にイメージを作成したときにはノード定義ファイルにある `files:` で指定したファイルが生成されます。

そのうちの一つが `config.json` で、Dockerに対する指示はここに書かれています。

```YAML
    files:
      - name: config.json
        editable: false
        content: |
          {
            "docker": {
              "image": "frr:10.2.1-r1",
              "mounts": [
                "type=bind,source=cfg/boot.sh,target=/config/boot.sh",
                "type=bind,source=cfg/node.cfg,target=/config/node.cfg",
                "type=bind,source=cfg/protocols,target=/config/protocols"
              ],
```

上記のように config.json では起動するイメージ名を指定していますので、
同じノード定義ファイルでイメージ定義だけ差し替える、ということはできないことになります
（実際にやってみたら、できませんでした）。

<br>

> [!NOTE]
>
> ノード定義ファイルの中にある image: の部分はdockerのイメージ名です。イメージ定義のIDではありません。

<br>

独自で作成したdockerイメージをCMLに登録するには、ノード定義とイメージ定義の両方を作らないといけません。

<br><br><br>

今度は起動中のFRRイメージにシェルで接続してみます。

```bash
root@cml-controller:~# docker ps
CONTAINER ID   IMAGE           COMMAND       CREATED         STATUS         PORTS     NAMES
5038c95009ce   frr:10.2.1-r1   "/start.sh"   3 minutes ago   Up 3 minutes             894b8a48-3a9f-46d9-bf9f-c3d649dac49c

root@cml-controller:~# docker exec -it 5038c95009ce bash

frr-0:/# cat /etc/os-release
NAME="Alpine Linux"
ID=alpine
VERSION_ID=3.21.3
PRETTY_NAME="Alpine Linux v3.21"
HOME_URL="https://alpinelinux.org/"
BUG_REPORT_URL="https://gitlab.alpinelinux.org/alpine/aports/-/issues"
```

CML2.9に同梱されているFRRのイメージはAlpineをベースにしていることがわかります。

`/start.sh` が実行されているので、その中身を確認してみます。

このファイルはコンテナの中に焼かれていますので、ビルド時にコピーして渡しているはずです。

このファイルは流用したいので、取り出して保存しておきます。

[start.sh](/frr/start.sh) の中身はこの通りです。

```bash
#!/bin/bash

CONFIG=/config/node.cfg
BOOT=/config/boot.sh
PROTOCOLS=/config/protocols

# Not needed for Docker
# for iface in /sys/class/net/*; do
#   iface_name=$(basename "$iface")
#   if /usr/sbin/ethtool "$iface_name" &>/dev/null; then
#     /usr/sbin/ethtool -K "$iface_name" tx off
#   fi
# done

# enable the requested protocols
while IFS= read -r line; do
    line=$(echo "$line" | xargs) # no whitespace
    if [[ -n "$line" && ! "$line" =~ ^# ]]; then
        sed -r -e "s/^(${line}=)no$/\1yes/" -i /etc/frr/daemons
    fi
done <"$PROTOCOLS"

# day0 config for the router
if [ -f $CONFIG ]; then
    cp $CONFIG /etc/frr/frr.conf
fi

# set the hostname from the provided config if it's there
hostname_value="router"
if grep -q "^hostname" $CONFIG; then
    hostname_value=$(awk '/^hostname/ {print $2}' $CONFIG)
fi
hostname $hostname_value

/usr/lib/frr/frrinit.sh start

echo "READY" >/dev/console

trap '' INT TSTP
while true; do
    /usr/bin/vtysh
done
```

コンテナの中の /config ディレクトリには確かにファイルが３個あります。

```bash
frr-0:/# ls /config
boot.sh    node.cfg   protocols
frr-0:/#
```

これらファイルはdocker起動時にマウントされて渡されたもので、
イメージをインスタンス化したときに作られるディレクトリ、
すなわちCML本体の `/var/local/virl2/images/{{ラボのUUID}}/{{イメージのUUID}}/cfg` に実物が置かれています。

<br><br>

以上のことから、Ubuntu24ベースでコンテナをビルドするには、以下のようなDockerfileを作ればよさそうです。

```dockerfile
# Dockerfile for building FRRouting (FRR) on Ubuntu 24.04

ARG UBUNTU_VERSION=24.04
FROM ubuntu:$UBUNTU_VERSION

# Based on the official FRR documentation for building on Ubuntu 24.04
# https://docs.frrouting.org/projects/dev-guide/en/latest/building-frr-for-ubuntu2404.html

ENV TZ Asia/Tokyo
ENV LANG ja_JP.UTF-8
ENV WORKING_DIRECTORY /root

ENV DATE 20250817

WORKDIR $WORKING_DIRECTORY

USER root

RUN apt update \
    && apt upgrade -y \
    && apt install -y \
            git autoconf automake libtool make libreadline-dev texinfo \
            pkg-config libpam0g-dev libjson-c-dev bison flex \
            libc-ares-dev python3-dev python3-sphinx \
            install-info build-essential libsnmp-dev perl \
            libcap-dev libelf-dev libunwind-dev \
            protobuf-c-compiler libprotobuf-c-dev \
    # Install libyang build requirements
    && apt install -y cmake libpcre2-dev \
    # Install libyang
    && git clone https://github.com/CESNET/libyang.git \
    && cd libyang \
    && git checkout v2.1.128 \
    && mkdir build; cd build \
    && cmake --install-prefix /usr -D CMAKE_BUILD_TYPE:String="Release" .. \
    && make \
    && make install \
    && cd ${WORKING_DIRECTORY} \
    # Install GRPC
    && apt install -y libgrpc++-dev protobuf-compiler-grpc \
    # Install Config Rollbacks
    && apt install -y libsqlite3-dev \
    # ZeroMQ
    && apt install -y libzmq5 libzmq3-dev \
    # utilities
    && apt install -y vim \
    # Add FRR user and groups
    && groupadd -r -g 92 frr \
    && groupadd -r -g 85 frrvty \
    && adduser --system --ingroup frr --home /var/run/frr/ --gecos "FRR suite" --shell /sbin/nologin frr \
    && usermod -a -G frrvty frr \
    # Compile
    && export GIT_SSL_NO_VERIFY=true \
    && cd ${WORKING_DIRECTORY} \
    && git clone https://github.com/frrouting/frr.git frr \
    && cd frr \
    && ./bootstrap.sh \
    && ./configure \
            --includedir=/usr/include \
            --bindir=/usr/bin \
            --sbindir=/usr/lib/frr \
            --libdir=/usr/lib/frr \
            --libexecdir=/usr/lib/frr \
            --sysconfdir=/etc \
            --localstatedir=/var \
            --with-moduledir=/usr/lib/frr/modules \
            --enable-configfile-mask=0640 \
            --enable-logfile-mask=0640 \
            --enable-snmp \
            --enable-multipath=64 \
            --enable-user=frr \
            --enable-group=frr \
            --enable-vty-group=frrvty \
            --with-pkg-git-version \
            --with-pkg-extra-version=-${DATE} \
            --disable-doc \
    && make \
    && make install \
    && install -m 775 -o frr -g frr -d /var/log/frr \
    && install -m 775 -o frr -g frr -d /etc/frr \
    && install -m 640 -o frr -g frr tools/etc/frr/vtysh.conf /etc/frr/vtysh.conf \
    && install -m 640 -o frr -g frr tools/etc/frr/frr.conf /etc/frr/frr.conf \
    && install -m 640 -o frr -g frr tools/etc/frr/daemons.conf /etc/frr/daemons.conf \
    && install -m 640 -o frr -g frr tools/etc/frr/daemons /etc/frr/daemons \
    && install -m 640 -o frr -g frr tools/etc/frr/support_bundle_commands.conf /etc/frr/support_bundle_commands.conf \
    # Clean up
    && apt remove -y \
    && apt clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/lib/cache/* \
    && rm -rf ${WORKING_DIRECTORY}/frr \
    && rm -rf ${WORKING_DIRECTORY}/libyang \
    # Enable IPv6 forwarding
    && sed -i '/^net.ipv6.conf.all.forwarding/s/^.*$/net.ipv6.conf.all.forwarding=1/' /etc/sysctl.conf \
    && grep -q '^net.ipv6.conf.all.forwarding=1' /etc/sysctl.conf || echo 'net.ipv6.conf.all.forwarding=1' >> /etc/sysctl.conf

COPY --chmod=0755 start.sh /

CMD ["/start.sh"]
```

<br><br><br><br><br><br>

# 【参考】コンテナ内でIPv6中継を有効にする試み

CML2.9に同梱のFRRを起動しても、IPv6中継機能が動作しません。

結論としては、ノード定義ファイルの中に記載するconfig.jsonに`run_args`というオプションを追記して、docker create時に `--sysctl net.ipv6.conf.all.forwarding=1` を渡してあげる必要があります。

<br>

## dockerコマンドでイメージを走らせてみる（--sysctlなし）

母艦となっているCMLでdockerコマンドを使ってコンテナを起動してみます。

- docker run

```bash
root@cml-controller:~# docker run -d --rm frr:10.5-iida
7b5766d395baf26a4b0ad44fb1e159ca39a51d0da8bf7de2235255b9dbdf95b5

root@cml-controller:~# docker ps
CONTAINER ID   IMAGE           COMMAND       CREATED          STATUS          PORTS     NAMES
7b5766d395ba   frr:10.5-iida   "/start.sh"   56 seconds ago   Up 55 seconds             festive_lehmann

root@cml-controller:~# docker exec -it 7b5766d395ba bash

root@7b5766d395ba:~# sysctl net.ipv6.conf.all.forwarding
net.ipv6.conf.all.forwarding = 0

exit

root@cml-controller:~# docker stop 7b5766d395ba
```

そのまま走らせただけではIPv6の中継機能は動いてくれません。

<br>

## dockerコマンドでイメージを走らせてみる（--sysctlあり）

今度は`--sysctl`を引数に与えて起動してみます。

- docker run --sysctl

```bash
root@cml-controller:~# docker run -d --rm --sysctl net.ipv6.conf.all.forwarding=1 frr:10.5-iida
aa016aa57fa5cdbf1bf0400f1b021cdcd284f86200b11e489384846b4ffab4e5
```

- docker ps

```bash
root@cml-controller:~# docker ps
CONTAINER ID   IMAGE           COMMAND       CREATED          STATUS          PORTS     NAMES
aa016aa57fa5   frr:10.5-iida   "/start.sh"   36 seconds ago   Up 35 seconds             stupefied_curran
```

- docker exec

```bash
root@cml-controller:~# docker exec -it  aa016aa57fa5 bash
```

- sysctl

```bash
root@aa016aa57fa5:~# sysctl net.ipv6.conf.all.forwarding
net.ipv6.conf.all.forwarding = 1
```

無事にIPv6の中継機能が動きました。

docker runで起動する時に `--sysctl` を付ければよいことがわかります。

また、dockerコマンドを直接叩けばコンテナ内でIPv6ルーティングできることから、
CMLの母艦になっているUbuntu自体には問題がないこともわかります。

<br>

## CMLのDockerコンテナでIPv6中継を有効にする試み

CMLにおけるdockerイメージの起動は、dockerコマンドを直接叩いているわけではなく、CML独自のラッパーを経由しています。
これはWebの設定画面で作成したnode.cfgやprotocolsなど、任意の設定ファイルをコンテナに渡せるようにするためで、
それが `/usr/lib/systemd/system/virl2-docker-shim.service` というサービスです。

このサービスのファイルを見てみると、どうやら `/etc/default/docker-shim.env` に設定があるようです。

docker-shim.envを見てみると、コンテナで最初に実行するスクリプトの権限を設定できるようです。

```text
# The way this works can be configured using the -day0privs flag with the
# following options:
#
# 1) keep: If this is specified, then no additional privileges are granted when
#    running the day0 script.  Whatever is specified in the Docker specific
#    caps section of the node definition is kept.  Network configuration might
#    not be possible
# 2) netadmin: This is the default and specifically adds the CAP_NET_ADMIN
#    capabilities to the CML node container configuration unless it hasn't been
#    provided to the container already in the "caps" list of the Docker
#    specific properties of the node definition
# 3) privileged: in this case, the day0 script will run with privileges inside
#    the container.  Note that this might be considered a security problem
#    especially for multi-user CML installations. RUNNING CONTAINERS PRIVILEGED
#    IS CONSIDERED INSECURE. ONLY DO THIS IF YOU TRUST EVERY USER ON YOUR CML
#    SYSTEM!
```

初期値（省略した場合）はnetadminになります。

コンテナ内でIPv6の中継を有効にするには初期値のnetaminでは権限が足りない可能性がありますので、`-day0privs privileged` をOPTSに加えてみます。

```bash
vi /etc/default/docker-shim.env
```

最終行の

```text
OPTS="-base /var/local/virl2/images ...
```

の部分を

```text
OPTS="-day0privs privileged -base /var/local/virl2/images ...
```

のように書き換えます。
これでコンテナにprivilege権限が付与され、boot.shは特権で実行されます。

続いてノード定義ファイルを編集してboot.shに `sysctl -w net.ipv6.conf.all.forwarding=1` を実行するように書き加えます。

再起動します。

```bash
reboot
```

あらためてラボのFRRのイメージをインスタンス化してみたのですが、残念ながら結果は変わらず。

`/var/local/virl2/images/{{ ラボのUUID }}/{{ イメージのUUID }}/day0.log` を見てみると、次のようになっています。

```bash
cat day0.log
!net.ipv6.conf.all.forwarding = 1
Tsysctl: setting key "net.ipv6.conf.all.forwarding", ignoring: Read-only file system
```

boot.shの中でsysctlを走らせるのはタイミング的に遅すぎなんだと思います。
いくら特権を持っていてもリードオンリーでマウントされたファイルシステムには書き込めません。

<br>

## dockerdの設定を変えてみる（失敗）

CMLにおけるdockerのサービスは　`/usr/lib/systemd/system/docker.service`　で起動されていますので、
このファイルを直接書き換えて `--ipv6 --ip-forward-no-drop --ip6tables=false` を加えてデーモンを起動してみます。

他にもオプションをいろいろ試しましたが、いずれもうまくいきませんでした。

このファイルを変更する必要はありません。

<br>

## サービス `sysctldisableipv6` を停止してみる（失敗）

コックピットでプロセスを確認すると　`sysctldisableipv6`　という謎のプロセスが走っています。

このサービスをkillしてからFRRイメージを動かしてみましたが、結果は変わりませんでした。

おそらくこれはvirl2-fabricに紐づいて起動しているもので、dockerとは無関係と思われます。

<br>

## ノード定義ファイルにmisc_argsを追加する（失敗）

Dockerを使う別のノード定義ファイルを覗いてみるとmisc_argsを指定しているものがあります。

たとえば、thousandeyesの場合はこんな感じで指定しています。

```yaml
              "misc_args": [
                "--memory-swap=2g",
                "--shm-size=512m"
              ],
```

これをまねてFRRのノード定義ファイルにmisc_argsを追加して--sysctlオプションを書いてみます。

```yaml
    files:
      - name: config.json
        editable: false
        content: |
          {
            "docker": {
              "image": "frr:10.5-iida",
              "misc_args": [
                "--sysctl net.ipv6.conf.all.forwarding=1"
              ]
            },
```

このように書いてしまうと、実際のところイメージは起動しなくなるのですが、そのときの/var/log/syslogには次のようなエラーが記録されます。

```bash
cml-controller docker-shim[112054]:  ERROR output id: 15403b14-74df-4c63-862e-bb1e1d149fd6
 err: exit status 125
 stderr: "unknown flag: --sysctl net.ipv6.conf.all.forwarding\n\n
 Usage:  docker create [OPTIONS] IMAGE [COMMAND] [ARG...]\n\n
 Run 'docker create --help' for more information\n"
```

どうやらmisc_argsで指定した文字列はdocker-shimに渡されて、さらにそこから `docker create` が呼び出されて使われるようです。

misc_args以外に指定できるオプションがないか、 `strings /usr/local/bin/docker-shim` で探してみます。

```bash
root@cml-controller:/usr/local/bin# strings docker-shim | grep _args
json:"run_args,omitempty"
json:"misc_args,omitempty"
json:"name_args,omitempty"
json:"extra_args,omitempty"
```

run_argsがそれっぽいです。

<br>

## ノード定義ファイルにrun_argsを追加する（成功）

ノード定義ファイルにrun_argsを書いてみます。

```yaml
"run_args": [
  "--sysctl net.ipv6.conf.all.forwarding=1"
]
```

これもmisc_argsのときと同じく、docker createに渡されてエラーになってしまいます。

ちょっと書き方を変えてみます。

```yaml
"run_args": [
  "--sysctl", "net.ipv6.conf.all.forwarding=1"
]
```

するとうまくいきました！！！


<br><br><br><br><br><br>

# 【参考】Alpine版をビルドする

DockerをインストールしたUbuntu24にログインします。

githubからソースコードをクローンします。

```bash
mkdir src
cd src
git clone https://github.com/frrouting/frr.git -b stable/10.4
cd frr
```

apkを作成します。

```bash
./docker/alpine/build.sh
```

これで `./docker/alpine/pkgs/apk/x86_64/` にapkファイルが作成されます。

ディレクトリを変えます。`~/build`を作成して移動します。

```bash
mkdir -p ~/build
cd ~/build
```

必要なファイルを取ってきます。

```bash
curl -H 'Cache-Control: no-cache' -Ls https://raw.githubusercontent.com/takamitsu-iida/expt-cml/refs/heads/master/frr/Dockerfile.alpine --output Dockerfile

curl -H 'Cache-Control: no-cache' -Ls https://raw.githubusercontent.com/takamitsu-iida/expt-cml/refs/heads/master/frr/start.sh --output start.sh

cp ~/src/frr/docker/alpine/pkgs/apk/x86_64/* .
```

ビルドします。

```bash
docker build --rm -f ./Dockerfile -t frr:10.4 .
```

`docker images` でイメージを確認します。

実行例。

```bash
cisco@ubuntu-0:~/build$ docker images
REPOSITORY   TAG       IMAGE ID       CREATED         SIZE
frr          10.4      310cd34f991e   9 seconds ago   120MB
```

実行

```bash
docker run -d -it --rm --name frr frr:10.4
```

動作確認

```bash
docker exec -it frr bash
```

停止

```bash
docker stop frr
```

インスペクトしてIDを確認

```bash
docker inspect frr:10.4 | grep -i sha256 | head -n 1 | awk '{print $2}'
```

実行例

```bash
cisco@ubuntu-0:~/build$ docker inspect frr:10.4 | grep -i sha256 | head -n 1 | awk '{print $2}'
"sha256:3b4b958f319fecdcbe8f8207447f4ad812e6ff0d76734bf412c75451bfcb44bb",
```

保存

```bash
docker save -o frr.tar frr:10.4
gzip frr.tar
```

CMLのdropfolderにイメージを転送

```bash
scp frr.tar.gz admin@192.168.122.212:
```

コックピットのターミナルに移動

```bash
ssh 192.168.122.212 -p 1122
```

ルート特権を取る

```bash
sudo -s -E
```

ノード定義ファイルの場所に移動

```bash
cd /var/lib/libvirt/images/node-definitions/
```

ノード定義ファイルをダウンロード

```bash
curl -H 'Cache-Control: no-cache' -Ls https://raw.githubusercontent.com/takamitsu-iida/expt-cml/refs/heads/master/frr/cml_node_definition_alpine.yaml --output frr-10-4-iida.yaml

chown libvirt-qemu:virl2 frr-10-4-iida.yaml
```

イメージ定義ファイルの場所に移動

```bash
cd /var/lib/libvirt/images/virl-base-images/
```

dropfolderからイメージを移動、イメージ定義ファイルをダウンロード

```bash
mkdir -p frr-10-4-iida
chown libvirt-qemu:virl2 frr-10-4-iida
cd frr-10-4-iida
mv /var/local/virl2/dropfolder/frr.tar.gz .
chown libvirt-qemu:virl2 frr.tar.gz
curl -H 'Cache-Control: no-cache' -Ls https://raw.githubusercontent.com/takamitsu-iida/expt-cml/refs/heads/master/frr/cml_image_definition_alpine.yaml --output frr-10-4-iida.yaml
chown libvirt-qemu:virl2 frr-10-4-iida.yaml
```

イメージ定義ファイルのsha256をインスペクトした値に置き換える。

```bash
vi frr-10-4-iida.yaml
```

サービスを再起動

```bash
systemctl restart virl2.target
```

これでAlpineをベースにしたFRR(Docker)が登録され、使えるようになります。

ですが、Alpineベースのイメージはバージョン10.4でも挙動不審です。

サイズは大きくてもUbuntuベースでビルドした方が良さそうです。


<br><br><br><br><br><br>

# 参考文献

<br>

[Docker Engine version 28 release notes](https://docs.docker.com/engine/release-notes/28/)

DockerでのIPv6まわりの挙動は頻繁に更新されています。リリースノートのページを開いてIPv6で検索するとよいでしょう。

<br>

[Docker privileged オプションについて](https://qiita.com/muddydixon/items/d2982ab0846002bf3ea8)

Dockerイメージのノード定義ファイルで作成するconfig.jsonでは、
"caps"という項目でコンテナに割り当てる権限を列挙します。

どんな権限があるのか、は上記に記載されています。

<br>

[Docker on a router](https://docs.docker.com/engine/network/packet-filtering-firewalls/#docker-on-a-router)

Dockerの公式マニュアルです。コンテナがルータとして振る舞うときの動作について説明があります。

<br>

[https://docs.docker.com/reference/cli/dockerd/](https://docs.docker.com/reference/cli/dockerd/)

Dockerの公式マニュアルです。dockerdに与える引数の一覧です。
