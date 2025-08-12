# カスタムイメージを作成する

CMLに含まれるUbuntuのイメージはRead Onlyになっていますので、どれだけ変更しても元のイメージが変わることはありません。
そしてクローンできるのは元のイメージの方です。

かなり手間はかかりますが、お好きなアプリをインストールしたUbuntuイメージを作成してCMLに登録することもできます。

<br>

> [!NOTE]
>
> カスタマイズしたUbuntuの作り方は、この動画がわかりやすいです。
>
> https://www.youtube.com/watch?v=dCWwtKXMUuU

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

改造して使いたいのは `ubuntu-24-04-20250503` のイメージです。このディレクトリを属性付きでコピーします。

名前は何でも良いのですが、ここでは分かりやすく `-iida` を後ろに追加します。

```bash
cp -a ubuntu-24-04-20250503 ubuntu-24-04-20250503-iida
```

念の為、オーナーとグループをvirl2にします（-a付きのコピーなので、オーナーとグループも引き継いでいるはずです）。

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

- idの値はユニークである必要があるので必ず変更します。ディレクトリ名と一致させます。

- labelの値はGUIでOS選択するときにドロップダウンに表示されるので、分かりやすいものに変えます

- descriptionはlabelに合わせておきます

- read_onlyをtrueからfalseに変えます

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

NODE_DEF_ID=${COPY_DST}
NODE_DEF_LABEL="Ubuntu 24.04 - 3 May 2025 customized by iida"

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
sed -i -e "s/^id:.*\$/id: ${NODE_DEF_ID}/" ${COPY_DST}.yaml
sed -i -e "s/^label:.*\$/label: ${NODE_DEF_LABEL}/" ${COPY_DST}.yaml
sed -i -e "s/^description:.*\$/description: ${NODE_DEF_LABEL}/" ${COPY_DST}.yaml

systemctl restart virl2.target

cat ${COPY_DST}.yaml
```

実行は簡単です。
コックピットのターミナルで以下をコピペするだけです。

```bash
curl -H 'Cache-Control: no-cache' -Ls https://raw.githubusercontent.com/takamitsu-iida/expt-cml/refs/heads/main/bin/copy_node_definition.sh | bash -s
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

`bin/cml_create_lab1.py` を実行すると "cml_create_lab1" という名前のラボができます。

このラボを開始すると最新化された状態（apt update; apt dist-upgradeされた状態）でubuntuが起動します。

<br>
