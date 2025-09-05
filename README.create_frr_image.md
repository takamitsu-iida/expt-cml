# FRRをインストールしたUbuntuを作成する

CMLではUbuntuのイメージが提供されていますので、これをベースとしてカスタマイズして、CMLに登録します。

<br>

## 手順１．カスタマイズできるUbuntuのイメージ定義を作る

CMLに登録されているUbuntuのイメージはRead Onlyなので、変更可能なイメージを作成します。

<br>

[作り方の解説はこちら](/README.create_custom_image.md)

<br>

コックピットのターミナルに流し込むスクリプトを作ります。

```bash
#!/bin/bash

# 特権ユーザのシェルを取る
# パスワードを聞かれる
sudo -s -E

COPY_SRC="ubuntu-24-04-20250503"
COPY_DST="ubuntu-24-04-20250503-frr"

IMAGE_DEF_ID=${COPY_DST}
IMAGE_DEF_LABEL="Ubuntu 24.04 - 3 May 2025 with frr installed"

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
sed -i -e "s/^read_only:.*\$/read_only: false/" ${COPY_DST}.yaml

# virl2を再起動する
systemctl restart virl2.target

cat ${COPY_DST}.yaml
```

自分の場合はgithubにあるスクリプトを（書き換えることなくそのまま）実行すればよいので、
以下をコックピットのターミナルにコピペします。

```bash
curl -H 'Cache-Control: no-cache' -Ls https://raw.githubusercontent.com/takamitsu-iida/expt-cml/refs/heads/master/bin/copy_image_definition_iida.sh | bash -s
```

コックピットのターミナルに貼り付けて実行するのであれば、`sudo -s -E`で特権ユーザのシェルを手動で取ってから上記をコピペすればよいでしょう。

<br><br>

## 手順２．適当なラボでUbuntuを立ち上げる

`bin/cml_create_frr_ubuntu.py` を実行すると "frr_ubuntu" という名前のラボができます。

実行したときに表示されるメッセージは後ほど必要になります。

実行例。

```bash
(.venv) iida@s400win:~/git/expt-cml$ bin/cml_create_frr_ubuntu.py
SSL Verification disabled
2025-08-13 11:51:04,139 - INFO - To commit changes, execute following commands in cml cockpit terminal.

cd /var/local/virl2/images/427c1172-4aaa-4f0b-b0ef-d8900011fb54/e92b3b3a-aff9-4119-97a9-665c2aeb01ea
sudo qemu-img commit node0.img
```

このラボを開始すると最新化された状態（apt update; apt dist-upgradeされた状態）でUbuntuが起動します。

<br>

## 手順３．FRRをインストールする（手作業の場合）

ここからは起動したUbuntuで作業します。

最新のFRRをインストールするにはソースコードからコンパイルしなければいけませんので作業は多めです。

FRRのマニュアルに記載されている通りに実行します。

https://docs.frrouting.org/projects/dev-guide/en/latest/building-frr-for-ubuntu2204.html

<br>

> [!NOTE]
>
> CML2.9からUbuntuのバージョンが24になっています。正しい参照先はこちら
>
> https://docs.frrouting.org/projects/dev-guide/en/latest/building-frr-for-ubuntu2404.html

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
mkdir ~/src
cd ~/src

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

カーネル設定を変更するために `/etc/sysctl.conf `を編集します。

```bash
sudo vi /etc/sysctl.conf
```

以下2行のコメントを外してルーティングを有効にします。

```bash
# Uncomment the next line to enable packet forwarding for IPv4
net.ipv4.ip_forward=1

# Uncomment the next line to enable packet forwarding for IPv6
#  Enabling this option disables Stateless Address Autoconfiguration
#  based on Router Advertisements for this host
net.ipv6.conf.all.forwarding=1
```

IPルーティングを有効にするために再起動します。

```bash
sudo reboot
```

サービス起動用のファイルをインストールします。

```bash
cd ~/src/frr/frr

sudo install -m 644 tools/frr.service /etc/systemd/system/frr.service
sudo systemctl enable frr
```

FRRのデーモン設定を変更してfabricdを有効にします。

```bash
sudo vi /etc/frr/daemons
```

好きなプロトコルを `yes` に変更します。

```text
fabricd=yes
```

FRRサービスを起動します。

```bash
sudo systemctl start frr
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

その他、気が済むまでいじったらUbuntuを停止します。

<br>

## 手順３．FRRをインストールする（自動化する場合）

以上のように、FRRのインストール作業は大変です。

試行錯誤しながら繰り返し実行すると尚更ですので、FRRのインストール作業を自動化するansibleのプレイブックを作成しました。

これはroot権限で作業します。

Ubuntuにログインしてから以下を実行します。

```bash
sudo -s -E

git clone https://github.com/takamitsu-iida/expt-cml.git

cd expt-cml

ansible-playbook install-frr-playbook.yaml
```

このプレイブックの最後では `/var/lib/cloud/` ディレクトリを削除して、次に起動したときにcloud-initが走るようにしています。

何らかの理由でこの仮想マシンを再起動してしまうと再びcloud-initが走ってしまうので、再起動したときには `rm -rf /var/lib/cloud` を忘れずに実行します。

その他、気が済むまでいじったらUbuntuを停止します。

<br>

> [!NOTE]
>
> cloud-initのログは `/var/log/cloud-init.log` にあります。

<br>

> [!NOTE]
>
> cloud-initのansible-pullを使えば、このプレイブックを初回起動時に自動実行できますが、FRRのコンパイルに長い時間かかりますので、プレイブックは手動で実行したほうがよさそうです。

<br>

> [!NOTE]
>
> cloud-initでansible-pullを設定すると `/root/.ansible/pull` に展開されます。
> 期待通りにansible-pullが走っていないときは、そこにちゃんとリポジトリのプレイブック一式が展開されているか確認します。
> 再度プレイブックを走らせたいときも `/root/.ansible/pull` にあるプレイブックを実行します。

<br>

## 手順４．変更を反映する

`bin/cml_create_frr_ubuntu.py` を実行したときに表示されたメッセージをコックピットのターミナルで実行します。

このメッセージは `log/cml_create_frr_ubuntu.log` に残っていますので、確認します。

```bash
cat log/cml_create_frr_ubuntu.log
```

これでFRRがインストールされたイメージ定義が完成です！

<br>

> [!NOTE]
>
> CMLのラボでUbuntuを作成したときに　`Image Definition`　のドロップダウンから自分で作成したイメージを選びましょう。
> Automaticのままだと既定のUbuntuイメージが立ち上がってしまいます

<br>

> [!NOTE]
>
> FRRのvtyshには `sudo -s -E` でroot特権を獲得してから入ります。
