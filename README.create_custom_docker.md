# Dockerイメージを作成してCMLに登録する

CML2.9はDockerをサポートしています。

もちろん自分で作成したDockerイメージをCMLに登録して動作させることもできます。

ここではUbuntuをベースによく使うアプリをインストールしたDockerイメージを作成してCMLに登録してみます。

<br><br>

## DockerをインストールしたUbuntuを用意する

Dockerイメージをビルドする母艦が必要です。

母艦となるUbuntuにはaptであれやこれやインストールしなければいけませんので、
Pythonスクリプトで生成した方が簡単です。

[bin/cml_create_custom_docker.py](/bin/cml_create_custom_docker.py)を実行して作成します。

```bash
bin/cml_create_custom_docker.py
usage: cml_create_custom_docker.py [-h] [--create] [--delete] [--stop] [--start]

create docker image lab

options:
  -h, --help  show this help message and exit
  --create    Create lab
  --delete    Delete lab
  --stop      Stop lab
  --start     Start lab
```

ラボを作るときは `bin/cml_create_custom_docker.py --create` です。

初回起動時はcloud-initで必要なパッケージをまとめてインストールしますので、Ubuntuのセットアップに少々時間がかかります。

<br>

## Dockerエンジンをインストール

`bin/cml_create_custom_docker.py` を使ってラボを作成した場合、UbuntuにDockerエンジンがインストールされた状態で起動しますので、この作業は不要です。

別の環境で作業する場合は、以下の手順でDockerエンジンをインストールします。

Dockerのインストールに必要なツールをインストールします。

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

<br>

> [!NOTE]
>
> dockerコマンド早見表
>
> - `docker run --rm`　起動します。停止するとコンテナを削除します。
> - `docker ps -a`　止まっているものを含めてプロセスを確認
> - `docker stop`　停止
> - `docker rm`　削除
> - `docker image ls`　存在するイメージの確認
> - `docker rmi`　イメージを削除
> - `docker system prune --all`　キャッシュの削除、再ビルドする前に実行
> - `docker tag IMAGE_ID IMAGE_NAME:TAG`　作成済みイメージの名前とタグを変更
> - `docker exec -it ID bash`　シェルを起動
> - `docker logs ID`　ログを見ます

<br><br><br>

---

<br>

# Dockerイメージを作ってCMLに登録する流れ

以下の手番で作業します。

1. Dockerfileを作ります
1. docker build します
1. 動作確認して気にいったイメージになるまでビルドを繰り返します
1. docker inspectで完成したイメージのIDを調べます
1. イメージ定義ファイルにそのIDを転記します
1. ノード定義ファイルを作ります
1. docker saveでイメージをtar形式にまとめます
1. scpでノード定義、イメージ定義、イメージファイルをCMLに転送します
1. ノード定義を所定の場所に移します(/var/lib/libvirt/images/node-definitions の直下)
1. イメージ定義ファイルを格納するディレクトリを作成します(/var/lib/libvirt/images/virl-base-images の配下に作成)
1. イメージ定義ファイルを作成したディレクトリに格納します
1. イメージファイルを作成したディレクトリに格納します
1. virl2サービスを再起動します(systemctl restart virl2.target)

少々手番が多いので、できるだけ簡単に作業できるように環境やツールを整えます。

<br><br>

### 事前準備１．CMLでSSHサーバを有効にする

OpenSSHを有効にしていない場合のみ、コックピットで有効にしてください。ラジオボタンを有効にするだけです。

CMLのSSHサーバはポート1122で待ち受けています（ポート22はコンソールサーバになっています）。

<br>

### 事前準備２．SSHの公開鍵を送り込んでおく

SSHの鍵が作成済みか、確認します。

`~/.ssh/id_rsa` があれば作成済みです。

```bash
ls -al ~/.ssh
```

まだSSHの鍵を作っていない場合は新規で作成します。

```bash
ssh-keygen -t rsa -b 4096 -N "" -f ~/.ssh/id_rsa
```

次に公開鍵をCMLに送り込みます。

```bash
ssh-copy-id -p 1122 admin@192.168.122.212
```

これでパスワードなしでCMLにログインできるようになり、
SCPでファイルを転送する際もパスワードを聞かれずにすみますので自動化が進みます。

<br>

### 事前準備３．makeコマンドをインストールする

Dockerファイルを調整しながら繰り返しdocker buildを実行することになりますので、Makefileを作成の上、makeコマンドを使った方が楽です。

`bin/cml_create_custom_docker.py` でラボを作成した場合、makeコマンドはすでにインストールされています。

手動でラボを作った場合、makeコマンドは標準で入っていませんのでインストールします。

```bash
apt install -y make
```

<br><br>

[Makefile](/ubuntu_docker/Makefile)は以下のようになっていますので、これを見ながらdockerコマンドを叩いても結果は同じです。

```Makefile
.DEFAULT_GOAL := help
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

TAG ?= ubuntu24.04:20251010

# ファイル名・パスの変数化
IMAGE_TAR    = ubuntu24.04.20251010.tar
IMAGE_TAR_GZ = ubuntu24.04.20251010.tar.gz

# CMLのIPアドレス
CML_HOST = 192.168.122.212
CML_UPLOAD_DIR = /var/tmp

####################################################
# 以下、変更不要
####################################################
SOURCE_IMAGE_DEFINITION = cml_image_definition.yaml
SOURCE_NODE_DEFINITION = cml_node_definition.yaml
INSTALL_SCRIPT = cml_install_image.sh
SSH_OPTS = -p 1122 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
CONTAINER_NAME = ntools-test

build: ## Dockerイメージを作成する
	@docker build -t ${TAG} -f Dockerfile .


inspect: ## DockerイメージのIDをインスペクトして、image_definition.yamlおよびnode_definition.yamlを生成する
	@cp -f ${SOURCE_IMAGE_DEFINITION} image_definition.yaml
	@cp -f ${SOURCE_NODE_DEFINITION} node_definition.yaml
	@SHA256=$$(docker inspect ${TAG} | grep -o 'sha256:[0-9a-f]\{64\}' | head -n 1 | cut -d: -f2); \
	sed -i "s/^sha256:.*/sha256: $$SHA256/" image_definition.yaml; echo $$SHA256


save: ## Dockerイメージを保存する
	@rm -f $(IMAGE_TAR_GZ)
	@docker save -o $(IMAGE_TAR) ${TAG}
	@gzip $(IMAGE_TAR)


run: ## Dockerコンテナを起動する
	@docker run -d --rm --init --privileged --name ${CONTAINER_NAME} ${TAG}


shell: ## Dockerコンテナにシェルで入る
	@docker exec -it ${CONTAINER_NAME} bash


stop: ## Dockerコンテナを停止する
	@if [ -n "$$(docker ps -q -f name=${CONTAINER_NAME})" ]; then docker stop ${CONTAINER_NAME}; fi


prune: ## Dockerの不要なイメージを削除する
	@docker system prune -f --all


clean: ## Dockerイメージを削除する
	@if [ -n "$$(docker images -q)" ]; then docker rmi $$(docker images -q); fi
	@rm -f $(IMAGE_TAR_GZ)
	@rm -f image_definition.yaml
	@rm -f node_definition.yaml


upload: ## ubuntu_docker.tar.gzおよびノード定義ファイルをCMLにアップロードする
	@rsync -avz -e "ssh ${SSH_OPTS}" $(IMAGE_TAR_GZ) image_definition.yaml node_definition.yaml ${INSTALL_SCRIPT} admin@${CML_HOST}:${CML_UPLOAD_DIR}
```

<br><br><br>

## Dockerイメージを作成する

ゼロからDockerfileを作成するのは茨の道です。すでに作成したものがありますので、それを使いましょう。

このリポジトリをクローンします。

```bash
git clone https://github.com/takamitsu-iida/expt-cml.git
```

移動します。

```bash
cd expt-cml
cd ubuntu_docker
```

[Dockerfile](/ubuntu_docker/Dockerfile) を確認して、追加したいパッケージがあれば追加、不要なものは削除します。

<br>

ビルドします。長い時間かかります。

```bash
make build
```

作成したdockerイメージをインスペクトしてIdの値をイメージ定義ファイルに反映します。

```bash
make inspect
```

実行例。

```bash
cisco@ubuntu:~/expt-cml/ubuntu_docker$ make inspect
850be02d0660af16fb83eb1ba6f44aa346f3cf445bf80ef82fec40c3589b6adc
```

`make inspect` を実行すると、image_definition.yamlを作成して、SHA256: の部分にこの文字列を埋め込みます。

`make inspect` することでイメージ定義ファイルとノード定義ファイルが完成します。

<br>

次にイメージをtar.gz形式で保存します。ファイルサイズが大きいため、この処理も長い時間かかります。

```bash
make save
```

`make save` することでイメージファイルが完成します。

<br>

あとは、ノード定義, イメージ定義, イメージファイルの３点セットをCMLに送り込んで適切な場所に格納します。

前述の事前準備を済ませてあるなら、CMLはSSHサーバ(ポート1122番）が有効になっているはずです。

次のコマンドでCMLの/var/tmpにファイルを送り込みます。

```bash
make upload
```

もしCMLでSSHサーバを有効にしていない場合、手作業で以下の4個のファイルをアップロードします。

```bash
scp node_definition.yaml        admin@192.168.122.212:
scp image_definition.yaml       admin@192.168.122.212:
scp ubuntu24.04.20251010.tar.gz admin@192.168.122.212:
scp cml_install_image.sh        admin@192.168.122.212:
```

<br>

> [!NOTE]
>
> scpで転送する場合、場所は指定できません。dropfolderという特別な場所に保存されます。
>
> dropfolderの実体は `/var/local/virl2/dropfolder` です。

<br>

> [!NOTE]
>
> CMLにファイルをアップロードする方法は他にもあります。
>
> CMLのAPIをcurlで叩いてもいいのですが、
> 新規に送り込むときはPOST、すでに存在しているものを更新する場合はPUT、というようにメソッドを使い分けるのがめんどくさいです。
>
> Pythonのvirl2_clientを使ってもできます。
> スクリプト [cml_upload.py](/bin/cml_upload.py) を使えばノード定義、イメージ定義、イメージファイルをCMLに送り込めます。
>
> ```bash
> iida@s400win:~/git/expt-cml$ source /home/iida/git/expt-cml/.venv/bin/activate
> $ bin/cml_upload.py
> usage: cml_upload.py [-h] [--node-def NODE_DEF] [--image-def IMAGE_DEF] [--image-file IMAGE_FILE]
>
> upload node definition, image definition, and image file to CML
>
> options:
>   -h, --help            show this help message and exit
>   --node-def NODE_DEF     ノード定義ファイルのパス
>   --image-def IMAGE_DEF   イメージ定義ファイルのパス
>   --image-file IMAGE_FILE イメージファイル（tar.gzなど）のパス
> ```
>
> ですが、Pythonの環境を整えるのがめんどくさいので、前述の通り `make upload` で送り込むのが簡単です。

<br><br>

ここからはCMLのコックピットのターミナルに移ります（Webブラウザのターミナルよりも、SSHでポート1122に接続した方が快適です）。

ルート特権を取ります。

```bash
sudo -s -E
```

先程送り込んだファイル `cml_install_image.sh` を実行します。

`make upload` でファイルをCMLにアップロードした場合は、/var/tmpにファイルがありますので、以下のように実行します。

```bash
bash /var/tmp/cml_install_image.sh
```

個別にファイルをアップロードした場合は dropfolder にファイルがありますので、以下のように実行します。

```bash
bash /var/local/virl2/dropfolder/cml_install_image.sh
```

これでノード定義、イメージ定義、イメージファイルが適切な場所に格納され、実行したスクリプト自身も消去されます。

`cml_install_image.sh` の中身は以下のようになっていますので、これを見ながら手作業で作業しても構いません。

```bash
#!/bin/bash

NODE_DEF_ROOT=/var/lib/libvirt/images/node-definitions
NODE_DEF_FILENAME=ubuntu-24-04-docker.yaml

IMAGE_DEF_ROOT=/var/lib/libvirt/images/virl-base-images
IMAGE_DEF_DIR=ubuntu-24-04-docker
IMAGE_DEF_FILENAME=ubuntu-24-04-docker.yaml
IMAGE_NAME=ubuntu24.04.20251010.tar.gz

if [ -f /var/tmp/node_definition.yaml ]; then
    mv /var/tmp/node_definition.yaml ${NODE_DEF_ROOT}/${NODE_DEF_FILENAME}
    chown libvirt-qemu:virl2 ${NODE_DEF_ROOT}/${NODE_DEF_FILENAME}
else
    echo "node_definition.yaml not found."
fi

mkdir -p ${IMAGE_DEF_ROOT}/${IMAGE_DEF_DIR}

if [ -f /var/tmp/image_definition.yaml ]; then
    mv /var/tmp/image_definition.yaml ${IMAGE_DEF_ROOT}/${IMAGE_DEF_DIR}/${IMAGE_DEF_FILENAME}
else
    echo "image_definition.yaml not found."
fi

if [ -f /var/tmp/${IMAGE_NAME} ]; then
    mv /var/tmp/${IMAGE_NAME} ${IMAGE_DEF_ROOT}/${IMAGE_DEF_DIR}/${IMAGE_NAME}
else
    echo "${IMAGE_NAME} not found."
fi

chown -R libvirt-qemu:virl2 ${IMAGE_DEF_ROOT}/${IMAGE_DEF_DIR}

# スクリプト自身を削除
rm -- "$0"
```

<br>

最後にサービスを再起動します。

```
systemctl restart virl2.target
```

<br><br><br>

dockerのイメージがCMLに登録されているか、確認します。

```bash
root@cml-controller:/var/lib/libvirt/images/virl-base-images# docker images
REPOSITORY   TAG                IMAGE ID       CREATED        SIZE
tig          latest             a22fa06572b5   6 days ago     1.54GB
frr          10.4               85e983fe6ab7   7 days ago     1.07GB
net-tools    1.0.0              87941db3e26a   4 months ago   575MB
chrome       136.0.7103.113-1   b5297d4bc69b   4 months ago   734MB
nginx        3.38               a830707172e8   5 months ago   192MB
frr          10.2.1-r1          1bd2e82159f1   6 months ago   39.8MB
```

この時点では登録されていません。

CMLのダッシュボードに移ります。

`ubuntu 24.04 docker` をドラッグしてイメージを一つ作ってみます。

STARTで起動します。

コックピットでdockerのイメージを確認します。

```bash
root@cml-controller:/var/lib/libvirt/images/virl-base-images# docker images
REPOSITORY    TAG                IMAGE ID       CREATED        SIZE
ubuntu24.04   20251010           850be02d0660   12 hours ago   832MB
tig           latest             a22fa06572b5   6 days ago     1.54GB
frr           10.4               85e983fe6ab7   7 days ago     1.07GB
net-tools     1.0.0              87941db3e26a   4 months ago   575MB
chrome        136.0.7103.113-1   b5297d4bc69b   4 months ago   734MB
nginx         3.38               a830707172e8   5 months ago   192MB
frr           10.2.1-r1          1bd2e82159f1   6 months ago   39.8MB
```

イメージ `ubuntu24.04:20251010` 登録されました。

<br>

> [!NOTE]
>
> ラボでイメージをドラッグドロップした時点では何も起きていません。STARTで起動して初めてイメージが実体化されます。
>
> 実体は `/usr/local/virl2/images/{{ラボのUUID}}` に格納されます。


<br><br><br><br><br><br>

---

<br>

## 【参考】CML2.9のDockerの挙動を調査してみる

CMLはDockerをラッパーで包みこんで利用しています。その動作を実際の挙動から調べてみます。

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

ラボ内にイメージを作成するたびにこれらファイルが作られるということは、どこかでこれらファイルを作成するように指示してはずです。

それはどこだろう？？？

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

なるほど、疑問解消です。

先ほど確認したファイルの内容がノード定義ファイルの中に書かれてます。

どうやらラボ内にイメージを作成したときにはノード定義ファイルにある `files:` で指定したファイルが生成されるようです。

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

上記のように config.json では起動するdockerイメージを指定していますので、
同じノード定義ファイルでイメージ定義だけ差し替える、ということはできないことになります

実際にやってみたら、できませんでした。

明らかに不便な仕様なので、将来のバージョンアップで変わるかもしれません。

<br>

> [!NOTE]
>
> ノード定義ファイルの中にある image: の部分はdockerのイメージ名です。イメージ定義のIDではありません。

<br><br><br>

今度は起動中のFRRイメージに `docker exec -it <id> bash` で接続してみます。

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

中身はこの通りです。

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

<br>

コンテナの中の /config ディレクトリには確かにファイルが３個あります。

```bash
frr-0:/# ls /config
boot.sh    node.cfg   protocols
frr-0:/#
```

これらファイルはdocker起動時にマウントされて渡されたもので、
イメージをインスタンス化したときに作られるディレクトリ `/var/local/virl2/images/{{ラボのUUID}}/{{イメージのUUID}}/cfg` に実物が置かれています。

<br><br><br><br><br><br>

---

<br>

## 参考文献

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
