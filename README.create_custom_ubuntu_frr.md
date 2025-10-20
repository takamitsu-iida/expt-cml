# FRRをインストールしたUbuntuを作成する

<br>

CMLではUbuntuのイメージが提供されていますので、これをベースにカスタマイズして、CMLに登録します。

<br>

> [!NOTE]
>
> カスタマイズしたUbuntuイメージの作り方は[こちら](/README.create_custom_ubuntu.md)に解説があります。

<br><br>

## 手順１．カスタマイズ可能なUbuntuのイメージ定義を作る

CMLに登録されているUbuntuのイメージはRead Onlyになっていて変更を保存できません。

変更可能なイメージを作成します。

この作業はCMLの中での操作（SSHでポート1122に接続するか、コックピットのターミナルで操作）になります。

いくつかコマンドを叩くのですが、手間を省くためにシェルスクリプトにまとめます。

このリポジトリにある [copy_image_definition_frr.sh](https://raw.githubusercontent.com/takamitsu-iida/expt-cml/refs/heads/master/bin/copy_image_definition_frr.sh) がたたき台です。

githubからダウンロードして適宜編集します。

curlでダウンロードするにはこうします。

```bash
curl -H 'Cache-Control: no-cache' -Ls https://raw.githubusercontent.com/takamitsu-iida/expt-cml/refs/heads/master/bin/copy_image_definition_frr.sh --output copy_image_definition.sh
```

内容は以下のようになっています。

`COPY_DST`や`IMAGE_DEF_LABEL`など、好きな名前に書き換えます。

ここでは元のUbuntuのイメージ定義の名前に -frr を付けて作成することにします。

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

`sudo -s -E`で **rootのシェルを取ってから** このシェルスクリプトを実行します。

<br>

> [!NOTE]
>
> 自分の場合はgithubにある[スクリプト](/bin/copy_image_definition_frr.sh)を（書き換えることなくそのまま）実行すればよいので、以下をコックピットのターミナルでコピペします。
>
> ```bash
> curl -H 'Cache-Control: no-cache' -Ls https://raw.githubusercontent.com/takamitsu-iida/expt-cml/refs/heads/master/bin/copy_image_definition_frr.sh | bash -s
> ```

<br><br>

## 手順２．作成したイメージでUbuntuを立ち上げる

[cml_create_custom_ubuntu_frr.py](/bin/cml_create_custom_ubuntu_frr.py) を実行すると "create ubuntu with frr installed" という名前のラボができます。

実行したときに表示されるメッセージは後ほど必要になります（ログファイルが残りますので、いつでも確認できます）。

実行例。

```bash
(.venv) iida@s400win:~/git/expt-cml$ bin/cml_create_custom_ubuntu_frr.py
usage: cml_create_custom_ubuntu_frr.py [-h] [--create] [--delete] [--stop] [--start] [--testbed]

create lab to customize ubuntu(with frr)

options:
  -h, --help  show this help message and exit
  --create    Create lab
  --delete    Delete lab
  --stop      Stop lab
  --start     Start lab
  --testbed   Show pyATS testbed
```

<br>

--createでラボを作成します。このときに表示されるメッセージが重要です。

```bash
(.venv) iida@s400win:~/git/expt-cml$ bin/cml_create_custom_ubuntu_frr.py --create
2025-10-20 18:53:36,110 - INFO - To commit changes, execute following commands in cml cockpit terminal.

cd /var/local/virl2/images/e7be5509-500f-4b76-b928-4a99bc918575/5a4e4a74-f24e-41c2-bf4f-5b605071de04
sudo qemu-img commit node0.img
```

<br>

--startで開始します（ブラウザでSTARTボタンを押しても同じです）

```bash
(.venv) iida@s400win:~/git/expt-cml$ bin/cml_create_custom_ubuntu_frr.py --start
2025-10-20 18:55:49,238 - INFO - Lab 'frr_ubuntu' started
```

startedと表示されていますが、Ubuntuは初回起動時にcloud-initで必要なツール類をインストールしますので、この処理の完了まで長い時間かかります。

Ubuntuにログインしたら `cloud-init status` で状況を確認してください。

<br><br>

## 手順３．FRRをインストールする（手作業の場合）

ここからは起動したUbuntuで作業します。

このUbuntuには 'serial:6000' というタグを付けていますので、CMLのポート6000番にtelnetすればコンソールが開きます。

最新のFRRをインストールするにはソースコードからコンパイルしなければいけませんので作業は多めです。

FRRのマニュアルに記載されている通りに実行します。

https://docs.frrouting.org/projects/dev-guide/en/latest/building-frr-for-ubuntu2404.html

<br>

必要なパッケージをインストールします。

```bash
sudo apt update
sudo apt-get install -y \
   git autoconf automake libtool make libreadline-dev texinfo \
   pkg-config libpam0g-dev libjson-c-dev bison flex \
   libc-ares-dev python3-dev python3-sphinx \
   install-info build-essential libsnmp-dev perl \
   libcap-dev libelf-dev libunwind-dev \
   protobuf-c-compiler libprotobuf-c-dev
```

libyangをインストールします。libyangは新しいものが必要なのでソースコードからmakeします。

```bash
sudo apt install -y cmake
sudo apt install -y libpcre2-dev

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

# stable 10.4
git clone -b stable/10.4 https://github.com/FRRouting/frr.git frr

# latest
# git clone https://github.com/frrouting/frr.git frr

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
sudo install -m 640 -o frr -g frr tools/etc/frr/support_bundle_commands.conf /etc/frr/support_bundle_commands.conf
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

<br><br>

## 手順３．FRRをインストールする（自動化する場合）

以上のように、FRRのインストール作業は大変です。

試行錯誤しながら繰り返し実行すると尚更ですので、FRRのインストール作業を自動化するansibleのプレイブックを作成しました。

これはroot権限で作業します。

Ubuntuにログインしてから以下を実行します。インストール作業を行いますのでroot特権を取ってからansibleを実行します。

```bash
git clone https://github.com/takamitsu-iida/expt-cml.git

cd expt-cml
cd ubuntu_frr

sudo -s -E

ansible-playbook playbook.yaml
```

このプレイブックの最後では `/var/lib/cloud/` ディレクトリを削除して、次に起動したときにcloud-initが走るようにしています。

何らかの理由でこの仮想マシンを再起動してしまうと再びcloud-initが走ってしまいます。再起動したときには `rm -rf /var/lib/cloud` を忘れずに実行します。

その他、気が済むまでいじったら**Ubuntuを停止**します（停止した状態でないと変更を反映できません）。

<br>

> [!NOTE]
>
> cloud-initのansible-pullを使えば、このプレイブックを初回起動時に自動実行することもできます。
> ですが、FRRのコンパイルに長い時間かかりますし、失敗する恐れもありますので、プレイブックは手動で実行した方がよさそうです。
>
> もしansible-pullで初回起動時に実行した場合、playbook等は `/root/.ansible/pull` に展開されています。

<br><br>

## 手順４．変更を反映する

`bin/cml_create_custom_ubuntu_frr.py` でラボを作成したときに表示されたメッセージをコックピットのターミナルで実行します。

このメッセージが流れてしまっていても大丈夫です。`log/cml_create_custom_ubuntu_frr.log` に残っていますので、確認します。

```bash
cat log/cml_create_custom_ubuntu_frr.log
```

<br>

CMLのターミナルでroot特権を取ります。

```bash
sudo -s -E
```

コピペします。

例

```bash
root@cml-controller:~# cd /var/local/virl2/images/e7be5509-500f-4b76-b928-4a99bc918575/5a4e4a74-f24e-41c2-bf4f-5b605071de04
sudo qemu-img commit node0.img
Image committed.
root@cml-controller:/var/local/virl2/images/e7be5509-500f-4b76-b928-4a99bc918575/5a4e4a74-f24e-41c2-bf4f-5b605071de04#
```

これでFRRがインストールされたイメージ定義が完成です！

次回以降、ラボでUbuntuを作成したときに　`Image Definition`　のドロップダウンから自分で作成したイメージを選びましょう（Automaticのままだと既定のUbuntuイメージが立ち上がってしまいます）。

Ubuntu自体の設定は通常通りcloud-initで設定します（ダッシュボードのGUIのCONFIGから設定します）。

FRR自体の設定はログイン後に /etc/frr にあるファイルを編集します。

FRRのシェルに入るには、`sudo vtysh` です（root特権を取るのを忘れがち）。
