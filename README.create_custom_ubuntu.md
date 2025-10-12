# Ubuntuのカスタムイメージを作成する

CMLに含まれるUbuntuのイメージはRead Onlyになっていますので、どれだけ変更しても元のイメージが変わることはありません。
そしてクローンできるのは元のイメージの方です。

多少手間はかかりますが、好きなアプリをインストールしたUbuntuイメージを作成して、CMLに登録することもできます。

<br>

> [!NOTE]
>
> カスタマイズしたUbuntuの作り方は、この動画がわかりやすいです。
>
> https://www.youtube.com/watch?v=dCWwtKXMUuU

<br>

まずは全てを手作業で実施する前提で手順を書いていきます（自動化した手順は後述します）。

<br>

## 手順１．コックピットでUbuntuのイメージをコピーする

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

もしくはCMLでSSHを有効にしているなら、好きなターミナルでポート1122にSSHします。こちらの方がおすすめです。

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

CMLのバージョンによって同梱されるイメージは変わってきますので、元にしたいUbuntuのイメージを確認します。

```bash
root@cml-controller:/var/lib/libvirt/images/virl-base-images# ls -l
total 112
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 alpine-base-3-21-3
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 alpine-desktop-3-21-3
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 alpine-trex-3-21-3
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 alpine-wanem-3-21-3
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 asav-9-23-1
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 cat8000v-17-16-01a
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 cat9000v-q200-17-15-03
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 cat9000v-uadp-17-15-03
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 chrome-136-0-7103-113-1
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 csr1000v-17-03-08a
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 dnsmasq-2-9-0
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 firefox-138-0-4-build1
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 frr-10-2-1-r1
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 iol-xe-17-16-01a
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 iol-xe-17-16-01a-serial-4eth
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 ioll2-xe-17-16-01a
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 iosv-159-3-m10
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 iosvl2-2020
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 iosxrv9000-25-1-1
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 net-tools-1-0-0
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 nginx-3-38
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 nxosv9300-10-5-3-f
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 radius-3-2-1
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 server-tcl-16-0
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 syslog-3-38
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 tacplus-f4-0-4-28
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 thousandeyes-ea-1-210-0
drwxrwxr-x 2 libvirt-qemu virl2 4096 Aug 12 07:41 ubuntu-24-04-20250503
```

<br>

### Ubuntuのイメージをコピーする

改造して使いたいのは `ubuntu-24-04-20250503` のイメージです。このディレクトリをコピーします。

名前は何でも良いのですが、ここでは分かりやすく `-iida` を後ろに追加します。

```bash
cp -a ubuntu-24-04-20250503 ubuntu-24-04-20250503-iida
```

オーナーとグループをvirl2にします。

```bash
chown virl2:virl2 ubuntu-24-04-20250503-iida
```

<br>

### イメージ定義ファイルを修正する

コピーしたディレクトリに移動します。

```bash
cd ubuntu-24-04-20250503-iida
```

ここにはイメージファイルとイメージ定義ファイル（YAMLファイル）が置かれています。

イメージ定義ファイル（YAML形式のファイル）をディレクトリ名と一致するように変更します。

```bash
mv ubuntu-24-04-20250503.yaml ubuntu-24-04-20250503-iida.yaml
```

続いて内容を編集します。

```bash
vi ubuntu-24-04-20250503-iida.yaml
```

もとのYAMLはこうなっています。

```YAML
#
# Ubuntu 24.04 image definition (cloud image, using cloud-init)
# generated 2025-05-08
# part of VIRL^2
#

id: ubuntu-24-04-20250503
label: Ubuntu 24.04 - 3 May 2025
description: Ubuntu 24.04 - 3 May 2025
node_definition_id: ubuntu
disk_image: noble-server-cloudimg-amd64.img
read_only: true
schema_version: 0.0.1
```

- idの値はユニークである必要があるので必ず変更、**ディレクトリ名と一致させます**

- labelの値はGUIでOS選択するときにドロップダウンに表示されるので、分かりやすいものに変えます

- descriptionはlabelに合わせておきます

- node_definition_idの値はそのままにしておきます(GUIでubuntuとして作成して、起動イメージを切り替えて使います)

- disk_imageの値はそのままにしておきます

- **read_onlyをtrueからfalseに変えます**

編集後はこのようになります。

```YAML
#
# Ubuntu 24.04 image definition (cloud image, using cloud-init)
# generated 2025-05-08
# part of VIRL^2
#

id: ubuntu-24-04-20250503-iida
label: Ubuntu 24.04 - 3 May 2025 customized by iida
description: Ubuntu 24.04 - 3 May 2025 customized by iida
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

サービスを再起動しても稼働中のラボには影響しませんが、ブラウザでCMLにログインしていた場合は強制的にログアウトされます。

<br>

## 以上のコックピットでの作業を自動化するシェルスクリプト

実験中は試行錯誤しながらUbuntuのイメージを何度も作り変えますので、ここまでのコックピットでの作業をシェルスクリプトにしました。

スクリプトの中身は以下の通りです。

[copy_image_definition_iida.sh](/bin/copy_image_definition_iida.sh)

<br>

```bash
#!/bin/bash

# 特権ユーザのシェルを取る（事前に実行しておいた方が良い）
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
sed -i -e "s/^read_only:.*\$/read_only: false/" ${COPY_DST}.yaml

# virl2を再起動する
systemctl restart virl2.target

cat ${COPY_DST}.yaml
```

自分の場合はgithub上のシェルスクリプトを（改版せずにそのまま）実行するだけなので、コックピットのターミナルで `sudo -s -E` で特権を取ってから以下をコピペするだけです。

```bash
curl -H 'Cache-Control: no-cache' -Ls https://raw.githubusercontent.com/takamitsu-iida/expt-cml/refs/heads/master/bin/copy_image_definition_iida.sh | bash -s
```

中身を書き換える場合はシェルスクリプトをダウンロードして編集してください。
curlでダウンロードするにはこうします。

```bash
curl -H 'Cache-Control: no-cache' -Ls https://raw.githubusercontent.com/takamitsu-iida/expt-cml/refs/heads/master/bin/copy_image_definition_iida.sh --output copy_image_definition.sh
```

<br><br>

## 手順２．カスタマイズしたUbuntuを作成する

ここからはCMLのダッシュボードのGUIで作業します。

適当なラボを作り、インターネットに出ていける外部接続とUbuntuを作成します。

このときUbuntuのSETTINGSタブの `Image Definition` のドロップダウンから、**上記で作成したラベルのものを選んで起動**します。

起動したらアップデート、FRRのインストール、などなどを実行して好みのUbuntuに仕上げます。

最後に `/var/lib/cloud` ディレクトリを丸ごと消去します。これは次に起動したときにcloud-initが走るようにするためです。

```bash
sudo rm -rf /var/lib/cloud
```

Ubuntuをshutdownして停止してください。

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

node0.imgファイルは元のイメージからの変更を保持していますので、これを保存します。

```bash
qemu-img commit node0.img
```

念の為、ubuntuを起動しなおして動作確認してみます。

ラボのubuntuをwipeしてコンフィグを破棄して、再び起動すると、先ほど施した変更が反映された状態で起動します。

<br>

## Ubuntuをカスタマイズするためのラボを自動作成する

ラボを作って、外部接続を作って、Ubuntuを作って、起動イメージを変更して、外部接続と結線して・・・といった作業を手作業でやるのは面倒なので、Pythonで自動化します。

`bin/cml_create_custom_ubuntu.py` を実行すると "custom_ubuntu" という名前のラボができます。

このラボを開始すると最新化された状態（apt update; apt dist-upgradeされた状態）でubuntuが起動します。

実行例

```bash
(.venv) iida@s400win:~/git/expt-cml$ bin/cml_create_custom_ubuntu.py
SSL Verification disabled
2025-08-12 20:48:06,763 - INFO - To commit changes, execute following commands in cml cockpit terminal.

cd /var/local/virl2/images/0a17e568-c034-4f16-bb1b-9b463b8c25d4/d0396938-e30b-4d73-a859-7ffc296e3f78
sudo qemu-img commit node0.img
```

このUbuntuを好きなだけイジったら `/var/lib/cloud` ディレクトリを丸ごと消去して、次に起動したときにcloud-initが走るようにします（忘れがち）。

```bash
sudo rm -rf /var/lib/cloud
```

Ubuntuを停止します。

ラボ作成時に表示されたメッセージをコックピットのターミナルで実行します。

このメッセージは `log/cml_create_custom_ubuntu.log` に残っていますので、確認します。

```bash
cat log/cml_create_custom_ubuntu.log
```

例。

```bash
cd /var/local/virl2/images/0a17e568-c034-4f16-bb1b-9b463b8c25d4/d0396938-e30b-4d73-a859-7ffc296e3f78
sudo qemu-img commit node0.img
```

これで変更が確定しますので、次回以降このイメージ定義を使えば、カスタマイズされた状態のUbuntuが起動します。


<br><br><br>

# 手順まとめ

<br>

- CMLのコックピットのターミナルでUbuntuのイメージをコピーするシェルスクリプト(copy_image_definition_iida.sh)を実行する

- bin/cml_create_custom_ubuntu.py を実行してラボを作る

- ラボの中のUbuntuを好きなようにいじる

- `/var/lib/cloud` ディレクトリを丸ごと消去する

- Ubuntuを停止する

- コックピットのターミナルでqemu-img commit node0.imgを実行する（ラボ作成時に表示された場所で実行する）


<br><br>

> [!NOTE]
>
> 慣れてきたら、CMLに同梱されているUbuntuを直接書き換えてもいいと思います。
>
> 要はイメージ定義ファイルのreadonlyを外してから `sudo qemu-img commit node0.img` するだけです。
