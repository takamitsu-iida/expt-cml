# FRRをインストールしたUbuntuを作成する

CMLではUbuntuのイメージが提供されていますので、これをベースとしてカスタマイズして、CMLに登録します。

<br>

> [!NOTE]
>
> カスタマイズしたUbuntuの作り方は、この動画がわかりやすいです。
>
> https://www.youtube.com/watch?v=dCWwtKXMUuU

<br>

## カスタマイズできるUbuntuを作る

CMLに登録されているUbuntuのイメージはRead Onlyなので、変更可能なイメージを作成します。




この作業はCMLのコックピットで行います。

<br>

### コックピットのターミナルにログイン

コックピットはCMLのIPアドレスにポート番号9090をHTTPSで開きます。

すでにブラウザでCMLを開いているのであれば `TOOLS → System Administration` をたどると以下のような表示があるので、リンクをクリックすればコックピットのログイン画面が開きます。

```text
The Cockpit service runs independently of the CML2 platform,
and allows recovery in the event of a system issue.
It is available at https://192.168.122.212:9090 (opens in a new Tab/Window).
```

<br>

### ルート権限のシェルを開く

コックピットの左下に「端末」が見えるので、それをクリックしてターミナルを開きます。

ルート権限のシェルを起動するには以下のようにします。

```bash
sudo -s -E
```

ルート権限を取るとプロンプトが `$` から `#` に変わります。

<br>

### Ubuntuのイメージが格納されている場所に移動する

CMLにバンドルされているUbuntuのイメージは `/var/lib/libvirt/images/virl-base-images` にありますので、そこに移動します。

```bash
cd /var/lib/libvirt/images
cd virl-base-images
```

ここにはUbuntuだけでなく様々なイメージが保存されています。

```bash
oot@cml-controller:/var/lib/libvirt/images/virl-base-images# ls -l
total 68
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 alpine-base-3-20-3
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 alpine-desktop-3-20-3
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 alpine-trex-3-20-3
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 alpine-wanem-3-20-3
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 asav-9-22-1-1
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 cat8000v-17-15-01a
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 cat9000v-q200-17-15-01
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 cat9000v-uadp-17-15-01
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 csr1000v-17-03-08a
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 iol-xe-17-15-01
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 ioll2-xe-17-15-01
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 iosv-159-3-m9
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 iosvl2-2020
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 iosxrv9000-24-3-1
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 nxosv9300-10-5-1-f
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 server-tcl-15-0
drwxrwxr-x 2 libvirt-qemu virl2 4096 Feb 21 04:32 ubuntu-24-04-20241004
root@cml-controller:/var/lib/libvirt/images/virl-base-images#
```

<br>

### Ubuntuのイメージをコピーする

改造して使いたいのは `ubuntu-24-04-20241004` のイメージです。このディレクトリを属性付きでコピーします。

名前は何でも良いのですが、ここでは分かりやすく `-frr` を後ろに追加します。

```bash
cp -a ubuntu-24-04-20241004 ubuntu-24-04-20241004-frr
```

念の為、オーナーとグループをvirl2にします（-a付きのコピーなので、オーナーとグループも引き継いでいるはずです）。

```bash
chown virl2:virl2 ubuntu-24-04-20241004-frr
```

<br>

### イメージ定義ファイルを修正する

コピーしたディレクトリに移動します。

```bash
cd ubuntu-24-04-20241004-frr
```

ここにはイメージファイルとイメージ定義ファイル（YAMLファイル）が置かれています。

イメージ定義ファイル（YAML形式のファイル）をディレクトリ名と一致するように変更します。

```bash
mv ubuntu-24-04-20241004.yaml  ubuntu-24-04-20241004-frr.yaml
```

続いて内容を編集します。

```bash
vi ubuntu-24-04-20241004-frr.yaml
```

もとのYAMLはこうなっています。

```YAML
#
# Ubuntu 24.04 image definition (cloud image, using cloud-init)
# generated 2024-10-12
# part of VIRL^2
#

id: ubuntu-24-04-20241004
label: Ubuntu 24.04 - 04 Oct 2024
description: Ubuntu 24.04 - 04 Oct 2024
node_definition_id: ubuntu
disk_image: noble-server-cloudimg-amd64.img
read_only: true
schema_version: 0.0.1
```

- idの値はユニークである必要があるので必ず変更します。ディレクトリ名と一致させます。

- labelの値はGUIでOS選択するときにドロップダウンに表示されるので、分かりやすいものに変えます

- descriptionはlabelに合わせておきます

- read_onlyをtrueからfalseに変えます

編集後はこのようになります。

```YAML
#
# Ubuntu 24.04 image definition (cloud image, using cloud-init)
# generated 2024-10-12
# part of VIRL^2
#

id: ubuntu-24-04-20241004-frr
label: Ubuntu 24.04 - 04 Oct 2024 - with FRR installed
description: Ubuntu 24.04 - 04 Oct 2024 -with FRR installed
node_definition_id: ubuntu
disk_image: noble-server-cloudimg-amd64.img
read_only: false
schema_version: 0.0.1
```

<br>

### CMLのサービスを再起動する

新しく作成したディレクトリのノード定義ファイルを読み込ませるために、サービスを再起動します。

```bash
systemctl restart virl2.target
```

サービスを再起動しても稼働中のラボには影響しませんが、ブラウザでCMLにログインしていた場合、すべてログアウトされます。

<br>

## 以上のコックピットでの作業を自動化するシェルスクリプト

実験中は試行錯誤しながらUbuntuのイメージを何度も作り変えますので、
ここまでのコックピットでの作業をシェルスクリプトにしました。

スクリプトの中身は以下の通りです。

```bash
#!/bin/bash

# 特権ユーザのシェルを取る
# パスワードを聞かれる
sudo -s -E

COPY_SRC="ubuntu-24-04-20250503"
COPY_DST="ubuntu-24-04-20250503-iida"

IMAGE_DEF_ID=${COPY_DST}
IMAGE_DEF_LABEL="Ubuntu 24.04 - 3 May 2025 customized by iida"

# ubuntuイメージのある場所に移動する
cd /var/lib/libvirt/images/virl-base-images

# すでにターゲットのディレクトリがあるなら消す
rm -rf ${COPY_DST}

# 属性付きでubuntuディレクトリをコピー
cp -a ${COPY_SRC} ${COPY_DST}

# オーナーをvirl2にする
chown virl2:virl2 ${COPY_DST}

# 作成したディレクトリに移動
cd ${COPY_DST}

# ノード定義ファイルの名前をディレクトリ名と一致させる
mv ${COPY_SRC}.yaml ${COPY_DST}.yaml

# ノード定義ファイルを編集する
sed -i -e "s/^id:.*\$/id: ${IMAGE_DEF_ID}/" ${COPY_DST}.yaml
sed -i -e "s/^label:.*\$/label: ${IMAGE_DEF_LABEL}/" ${COPY_DST}.yaml
sed -i -e "s/^description:.*\$/description: ${IMAGE_DEF_LABEL}/" ${COPY_DST}.yaml

# virl2を再起動する
systemctl restart virl2.target

cat ${COPY_DST}.yaml
```

実行は簡単で、コックピットのターミナルで上記をコピペするだけです。

自分の場合はgithubにあるスクリプトを（書き換えることなくそのまま）実行すればよいので、
以下をコックピットのターミナルにコピペします。

```bash
curl -H 'Cache-Control: no-cache' -Ls https://raw.githubusercontent.com/takamitsu-iida/expt-cml/refs/heads/master/bin/copy_image_definition_iida.sh | bash -s
```

<br><br>

## 手順２．カスタマイズしたUbuntuを作成する

ここからはCMLのダッシュボードで作業します。

適当なラボを作り、インターネットに出ていける外部接続とUbuntuを作成します。

UbuntuのSETTINGSタブの `Image Definition` のドロップダウンから、上記で作成したラベルのものを選んでから起動します。

起動したらアップデート、FRRのインストール、などなどを実行して好みのUbuntuに仕上げます。

<br><br>

## 手順３．変更をイメージに反映する

この時点ではまだUbuntuの起動イメージは変更されていません。

作業した内容を元のイメージに反映させます。

再びコックピットに戻って作業します。

作成したラボのUbuntuイメージの場所に移動します。
この場所を見つけるのはちょっと大変です。
CMLのダッシュボードで当該ラボを開いた状態でURLの文字列をコピーします。

こんな感じのURLになっているはずです。

```text
https://192.168.122.212/lab/7fe8ece7-6b23-49f3-a852-519c9f0a843a
```

最後のUUIDの部分をコピーします（この場合は7fe8ece7-6b23-49f3-a852-519c9f0a843aがUUIDです）

コックピットのターミナルで `/var/local/virl2/images/{{uuid}}` に移動します（`{{uuid}}`の部分は先ほどコピーしたものに置き換えます）

もう一つ下のディレクトリに起動中のubuntuのイメージがあります。

```bash
root@cml-controller:/var/local/virl2/images/7fe8ece7-6b23-49f3-a852-519c9f0a843a/2aa37c69-fcdc-4eb0-8e26-e00a95e6676e# ls -l
total 3114176
drwxr-xr-x 2 virl2        virl2       4096 Feb 21 07:38 cfg
-rw-r--r-- 1 libvirt-qemu kvm       376832 Feb 21 07:38 config.img
-rw-r--r-- 1 virl2        virl2        159 Feb 21 07:38 config.yaml
-rw-r--r-- 1 libvirt-qemu kvm   3188523008 Feb 21 07:49 node0.img
```

node0.imgファイルは元のイメージからの変更を保持していますので、これを元のイメージに反映します。

```bash
qemu-img commit node0.img
```

念の為、ubuntuを起動しなおして動作確認してみます。

ラボのubuntuをwipeしてコンフィグを破棄して、再び起動すると、先ほど施した変更が反映された状態で起動します。

<br>

## Ubuntuをカスタマイズするためのラボを自動作成する

ラボを作って、外部接続を作って、Ubuntuを作って、起動イメージを変更して、外部接続と結線して・・・といった作業を手作業でやるのは面倒なので、Pythonで自動化します。

`bin/cml_create_frr_lab.py` を実行すると "create frr" という名前のラボができます。

このラボを開始すると最新化された状態（apt update; apt dist-upgradeされた状態）でubuntuが起動します。

<br>

## FRRをインストールする

最新のFRRをインストールするにはソースコードからコンパイルしなければいけませんので作業は多めです。

FRRのマニュアルに記載されている通りに実行します。

<br>

> [!NOTE]
>
> https://docs.frrouting.org/projects/dev-guide/en/latest/building-frr-for-ubuntu2204.html

<br>

必要なパッケージをインストールします。

```bash
sudo apt install \
   git autoconf \
   automake libtool make libreadline-dev texinfo \
   pkg-config libpam0g-dev libjson-c-dev bison flex \
   libc-ares-dev python3-dev python3-sphinx \
   install-info build-essential libsnmp-dev perl \
   libcap-dev libelf-dev libunwind-dev \
   protobuf-c-compiler libprotobuf-c-dev
```

libyangをインストールします。libyangは新しいものが必要なのでソースコードからmakeします。

```bash
sudo apt install cmake
sudo apt install libpcre2-dev

mkdir ~/src
cd ~/src

git clone https://github.com/CESNET/libyang.git
cd libyang
git checkout v2.1.128
mkdir build; cd build
cmake --install-prefix /usr -D CMAKE_BUILD_TYPE:String="Release" ..
make
sudo make install
```

GRPCをインストールします。

```bash
sudo apt-get install libgrpc++-dev protobuf-compiler-grpc
```

ロールバック機能を使うにはsqlite3が必要なのでインストールします。

```bash
sudo apt install libsqlite3-dev
```

ZeroMQをインストールします。これは任意ですが、実行しておきます。

```bash
sudo apt-get install libzmq5 libzmq3-dev
```

FRRのユーザとグループを作成します。

```bash
sudo groupadd -r -g 92 frr
sudo groupadd -r -g 85 frrvty
sudo adduser --system --ingroup frr --home /var/run/frr/ --gecos "FRR suite" --shell /sbin/nologin frr
sudo usermod -a -G frrvty frr
```

FRRをコンパイルします。

```bash
mkdir ~/src/frr
cd ~/src/frr

git clone https://github.com/frrouting/frr.git frr
cd frr

./bootstrap.sh

./configure \
    --prefix=/usr \
    --includedir=\${prefix}/include \
    --bindir=\${prefix}/bin \
    --sbindir=\${prefix}/lib/frr \
    --libdir=\${prefix}/lib/frr \
    --libexecdir=\${prefix}/lib/frr \
    --sysconfdir=/etc \
    --localstatedir=/var \
    --with-moduledir=\${prefix}/lib/frr/modules \
    --enable-configfile-mask=0640 \
    --enable-logfile-mask=0640 \
    --enable-snmp=agentx \
    --enable-multipath=64 \
    --enable-user=frr \
    --enable-group=frr \
    --enable-vty-group=frrvty \
    --with-pkg-git-version \
    --with-pkg-extra-version=-MyOwnFRRVersion

make

sudo make install
```

コンフィグファイルをインストールします。

```bash
sudo install -m 775 -o frr -g frr -d /var/log/frr
sudo install -m 775 -o frr -g frrvty -d /etc/frr
sudo install -m 640 -o frr -g frrvty tools/etc/frr/vtysh.conf /etc/frr/vtysh.conf
sudo install -m 640 -o frr -g frr tools/etc/frr/frr.conf /etc/frr/frr.conf
sudo install -m 640 -o frr -g frr tools/etc/frr/daemons.conf /etc/frr/daemons.conf
sudo install -m 640 -o frr -g frr tools/etc/frr/daemons /etc/frr/daemons
```

カーネル設定を変更します。

/etc/sysctl.confの以下2行のコメントを外してルーティングを有効にします。

```bash
# Uncomment the next line to enable packet forwarding for IPv4
net.ipv4.ip_forward=1

# Uncomment the next line to enable packet forwarding for IPv6
#  Enabling this option disables Stateless Address Autoconfiguration
#  based on Router Advertisements for this host
net.ipv6.conf.all.forwarding=1
```

IPルーティングを有効にするために再起動します。

サービス起動用のファイルをインストールします。

```bash
cd ~/src/frr/frr

sudo install -m 644 tools/frr.service /etc/systemd/system/frr.service
sudo systemctl enable frr
```

FRRのデーモン設定を変更してfabricdを有効にします。

`/etc/frr/daemons`

```text
fabricd=yes
```

FRRサービスを起動します。

```bash
systemctl start frr
```

FRRに入るにはvtyshを起動します。

```bash
sudo -s -E
vtysh
```

最後に `/var/lib/cloud` ディレクトリを丸ごと消去して、次に起動したときにcloud-initが走るようにします。

```bash
sudo rm -rf /var/lib/cloud
```

気が済むまでいじったらUbuntuを停止します。

<br>

## FRRのインストール作業を自動化する

以上のように、FRRのインストール作業は大変です。
試行錯誤しながら繰り返し実行すると尚更ですので、FRRのインストール作業を自動化するansibleのプレイブックを作成しました。

これはroot権限で作業します。

```bash
sudo -s -E

git clone https://github.com/takamitsu-iida/frr-on-cml.git

cd frr-on-cml

ansible-playbook playbook.yaml
```

このプレイブックの最後では `/var/lib/cloud/` ディレクトリを削除して、次に起動したときにcloud-initが走るようにしています。

何らかの理由でこの仮想マシンを再起動してしまうと再びcloud-initが走ってしまうので、再起動後には `rm -rf /var/lib/cloud` を忘れずに実行します。

<br>

> [!NOTE]
>
> cloud-initのansible-pullを使えば、このプレイブックを初回起動時に自動実行できますが、FRRのコンパイルに長い時間かかりますので、手動で実行したほうがよいでしょう。

<br>

> [!NOTE]
>
> cloud-initのログは `/var/log/cloud-init.log` にあります。

<br>

> [!NOTE]
>
> ansible-pullは `/root/.ansible/pull` に展開されます。
> 期待通りにansible-pullが走っていないときは、そこにちゃんとリポジトリのプレイブック一式が展開されているか確認します。
> 再度プレイブックを走らせたいときも `/root/.ansible/pull` にあるプレイブックを実行します。

<br><br><br>

# 爆速でFRRインストール済みUbuntuを作成する手順

最初に手探りで作業するのは仕方ないのですが、自動化するスクリプトを作成しておくと時間の節約になるだけでなく、応用範囲が広がります。

<br>

## コックピットにログインして、Ubuntuのイメージをコピーするシェルスクリプトを実行します

```bash
curl -H 'Cache-Control: no-cache' -Ls https://raw.githubusercontent.com/takamitsu-iida/frr-on-cml/refs/heads/main/bin/copy_node_definition.sh | bash -s
```

<br>

## Pythonスクリプト `bin/cml_create_frr_lab.py` を実行して "create frr" ラボを作ります

```bash
bin/cml_create_frr_lab.py
```

スクリプト実行時に表示されるメッセージは後で利用します。

<br>

## Ubuntuのコンソールに接続します

CMLのアドレスが192.168.122.212の場合はこれで作成したUbuntuのシリアルコンソールに接続します。

```bash
telnet 192.168.122.212 6000
```

<br>

## FRRをインストールするプレイブックを実行します

```bash
sudo -s -E

git clone https://github.com/takamitsu-iida/frr-on-cml.git
cd frr-on-cml

ansible-playbook playbook.yaml
```

<br>

## Ubuntuを停止します

```bash
shutdown -h now
```

<br>

## コックピットにログインして、イメージの変更をコミットします

`bin/cml_create_frr_lab.py` を実行したときに表示された手順をコックピットにコピペして実行します。

<br>

## ラボを作成します

`bin/cml_create_openfabric_lab.py` を実行すると、OpenFabricの動作を検証するためのラボを自動作成します。
