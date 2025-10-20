# FRR(Docker)イメージを作成してCMLに登録する

<br>

FRRをインストールしたDockerイメージを作成してCMLに登録します。

<br>

> [!NOTE]
>
> Dockerイメージを作ってCMLに登録する方法は [README.create_custom_docker.md](/README.create_custom_docker.md) を参考にしてください。
>
> FRRをコンパイルしてインストールする方法は [README.create_custom_ubuntu_frr](/README.create_custom_ubuntu_frr.md) を参考にしてください。

<br><br>

## CML2.9に含まれるFRR(Docker)について

CML2.9に同梱のFRR(Docker)は次のような特徴を持っています。

- Alpineをベースにしています
- FRRのバージョンは10.2です
- IPv6のルーティングはできません（CMLのノード定義ファイルの不備です）
- FRRの設定は永続されません（毎回初期化されます。これは単純なミスなのでそのうち直ると思います）
- 起動時に node.cfg をチェックして hostname コマンドが入っていたらDockerのホスト名に反映させています

<br>

## 作成するFRR(Docker)について

- Ubuntu24.04をベースにDockerイメージを作成します
- FRRの設定(frr.conf)を永続できるようにします
- IPv6中継できるようにします（sysctl net.ipv6.conf.all.forwarding=1を設定します）
- FRR stable 10.4 をコンパイルして作成します
- dockerイメージのタグ名はfrr:10.4とします
- CMLのノード定義名はfrr-10-4とします
- SNMPを有効にします
- FRRバージョン8以降はvtyshからシェルコマンドを呼び出せませんので、対策としてSSHで外部から乗り込めるようにします(アカウントはroot)

Ubuntuをベースにすることでイメージのサイズは大きくなってしまいますが、一度Dockerイメージが登録されれば以降のノード起動は高速かつ軽量なので気になることはないと思います。

将来のCMLのバージョンアップでノード定義の名前が重複するかもしれませんが、
そのときはCMLをインストールし直すので、またDockerイメージも作り直せばいいかな、と思います。

<br><br>

## CMLの母艦の設定

FRRを使う主な動機はOpenFabricやSRv6を動かしたい、というところにありますので、IPv6の中継も必要になります。

Dockerの仕様上、母艦となっているCMLでもIPv6中継が必要になります。

CMLのコックピットにログインしてターミナルを開きます。

root特権を取ります。

```bash
sudo -s -E
```

`/etc/sysctl.conf` を編集します。

```bash
vi /etc/sysctl.conf
```

`net.ipv6.ip_forward=1` と `net.ipv6.conf.all.forwarding=1` が有効になるように、コメントを外します。

```text
# Uncomment the next line to enable packet forwarding for IPv4
net.ipv4.ip_forward=1

# Uncomment the next line to enable packet forwarding for IPv6
#  Enabling this option disables Stateless Address Autoconfiguration
#  based on Router Advertisements for this host
net.ipv6.conf.all.forwarding=1
```

Dockerコンテナの中でVRFを使う場合は、母艦側でVRFのカーネルモジュールをロードします。
（恐らく初期状態のCMLは、VRFモジュールをロードしていないと思います）

```bash
root@cml-controller:~# lsmod | grep vrf
vrf                    40960  0
```

このように表示されていればロードされています。

もし何も表示されないようなら、以下のように設定を追加します。

```bash
echo "vrf" | sudo tee /etc/modules-load.d/vrf.conf
```

CML自身を再起動します。次回以降、カーネルにVRFモジュールが組み込まれます。

```bash
reboot
```

<br>

> [!NOTE]
>
> dockerdは起動時にホストがIPv6中継可能かどうかをチェックしていますので、`sysctl -p` で反映させただけではだめです。
> CMLそのものを再起動したほうが早いです。

<br><br>

## DockerをインストールしたUbuntuを用意する

Dockerイメージをビルドするための環境を作ります。

[bin/cml_create_custom_docker.py](/bin/cml_create_custom_docker.py)を使ってCMLの中に環境を整えます。

実行例。

```bash
iida@s400win:~/git/expt-cml$ bin/cml_create_custom_docker.py
usage: cml_create_custom_docker.py [-h] [--create] [--delete] [--stop] [--start]

create docker image lab

options:
  -h, --help  show this help message and exit
  --create    Create lab
  --delete    Delete lab
  --stop      Stop lab
  --start     Start lab
```

ラボの作成は --create です。

<br>

ラボを起動するとDockerエンジンがインストールされた状態のUbuntuが起動します。

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

<br><br><br><br><br>

---

<br>

## Dockerイメージを作成してCMLに登録します

このリポジトリをクローンします。

```bash
git clone https://github.com/takamitsu-iida/expt-cml.git
```

移動します。

```bash
cd expt-cml
cd docker_frr
```

繰り返しdockerイメージを作るときにはキャッシュが悪さをするかもしれませんので削除します（dockerインストール直後の場合は省略して構いません）。

```bash
docker system prune --all
```

Dockerfileの内容に従ってビルドします。長い時間かかります。10分以上かかります。

```bash
make build
```

作成したdockerイメージをインスペクトしてIdの値をイメージ定義ファイルに反映します。

実行例。

```bash
make inspect
```

実行例。

```bash
root@ubuntu-0:~/expt-cml/frr# make inspect
dcb26c9c1ba66cdb17c6d3b7e2d1952abffd96b832a855ad4dd7e4c559a76d71
```

`make inspect` を実行すると、image_definition.yamlを作成して、SHA256: の部分にこの文字列を埋め込みます。

次にイメージをtar.gz形式で保存します。ファイルサイズが大きいため、この処理も長い時間かかります。

```bash
make save
```

ファイルfrr.tar.gzが生成されます。

このfrr.tar.gzおよび作成したイメージ定義ファイル、ノード定義ファイルをまとめてCMLに転送します。

CMLでSSHサーバ(ポート1122番）を有効にしている場合、次のコマンドでCMLの/var/tmpに送り込みます。

```bash
make upload
```

<br><br><br>

ここからはコックピットのターミナルに移ります（Webブラウザのターミナルよりも、SSHで接続した方が快適です）。

ルート特権を取ります。

```bash
sudo -s -E
```

`make upload` でファイルをCMLにアップロードすると、/var/tmpにインストール用のシェルスクリプトがありますので、以下のように実行します。

```bash
bash /var/tmp/cml_install_image.sh
```

<br>

virl2を再起動します。

```
systemctl restart virl2.target
```


<br><br><br><br><br><br>

---

<br>

## 【参考】コンテナ内でIPv6中継を有効にする試み

CML2.9に同梱のFRRを起動しても、IPv6中継機能が動作しません。

結論としては、ノード定義ファイルの中に記載するconfig.jsonに`run_args`というオプションを追記して、docker create時に `--sysctl net.ipv6.conf.all.forwarding=1` を渡してあげる必要があります。

<br>

## dockerコマンドでイメージを走らせてみる（--sysctlなし）

母艦となっているCMLでdockerコマンドを使ってコンテナを起動してみます。

- docker run

```bash
root@cml-controller:~# docker run -d --rm frr:10.4
7b5766d395baf26a4b0ad44fb1e159ca39a51d0da8bf7de2235255b9dbdf95b5

root@cml-controller:~# docker ps
CONTAINER ID   IMAGE           COMMAND       CREATED          STATUS          PORTS     NAMES
7b5766d395ba   frr:10.4        "/start.sh"   56 seconds ago   Up 55 seconds             festive_lehmann

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
root@cml-controller:~# docker run -d --rm --sysctl net.ipv6.conf.all.forwarding=1 frr:10.4
aa016aa57fa5cdbf1bf0400f1b021cdcd284f86200b11e489384846b4ffab4e5
```

- docker ps

```bash
root@cml-controller:~# docker ps
CONTAINER ID   IMAGE           COMMAND       CREATED          STATUS          PORTS     NAMES
aa016aa57fa5   frr:10.4        "/start.sh"   36 seconds ago   Up 35 seconds             stupefied_curran
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
              "image": "frr:10.4",
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

CMLのdropfolder(/var/local/virl2/dropfolder/)にイメージを転送

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
curl -H 'Cache-Control: no-cache' -Ls https://raw.githubusercontent.com/takamitsu-iida/expt-cml/refs/heads/master/frr/cml_node_definition_alpine.yaml --output frr-10-4.yaml

chown libvirt-qemu:virl2 frr-10-4.yaml
```

イメージ定義ファイルの場所に移動

```bash
cd /var/lib/libvirt/images/virl-base-images/
```

dropfolder(/var/local/virl2/dropfolder/)からイメージを移動、イメージ定義ファイルをダウンロード


```bash
mkdir -p frr-10-4
chown libvirt-qemu:virl2 frr-10-4
cd frr-10-4
mv /var/local/virl2/dropfolder/frr.tar.gz .
chown libvirt-qemu:virl2 frr.tar.gz
curl -H 'Cache-Control: no-cache' -Ls https://raw.githubusercontent.com/takamitsu-iida/expt-cml/refs/heads/master/frr/cml_image_definition_alpine.yaml --output frr-10-4.yaml
chown libvirt-qemu:virl2 frr-10-4.yaml
```

イメージ定義ファイルのsha256をインスペクトした値に置き換える。

```bash
vi frr-10-4.yaml
```

サービスを再起動

```bash
systemctl restart virl2.target
```

これでAlpineをベースにしたFRR(Docker)が登録され、使えるようになります。

ですが、Alpineベースのイメージはバージョン10.4でも挙動不審です。

サイズは大きくてもUbuntuベースでビルドした方が良さそうです。



<!--

root@cml-controller:~# modprobe vrf

root@cml-controller:~# lsmod | grep vrf
vrf                    40960  0

起動時にvrfモジュールをロードするために、/etc/modules-load.dにファイルを作る

echo "vrf" | sudo tee /etc/modules-load.d/vrf.conf

-->