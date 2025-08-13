# FRR(Docker)でOpenFabricを検証する

CML2.9以降でDockerイメージが動作するようになっています。

2025年8月時点、FRRのDocker版のバージョンは `FRRouting 10.2.1` です。

このバージョンではOpenFabricはうまく動かないようです。

<br>

## ラボ構成

スクリプト `bin/cml_create_openfabric_docker_lab.py` を使ってCML内にラボを自動生成します。

<br>

![ラボ構成](/assets/openfabric_docker_lab.png)

<br>

## なんかおかしい

設定をみたときに　`no ipv6 forwarding`　となっていて、IPv6の中継ができなくなっています。

```text
R1# show run
Building configuration...

Current configuration:
!
frr version 10.2.1
frr defaults traditional
hostname R1
log syslog informational
no ipv6 forwarding
service integrated-vtysh-config
!
```

IPv6のリンクローカルアドレスを固定で設定しているのに、自動で割り当ててしまっています。

```text
R1# show int brief
Interface       Status  VRF             Addresses
---------       ------  ---             ---------
eth0            up      default         + fe80::5054:ff:fec9:be76/64
eth1            up      default         + fe80::1/64
eth2            up      default         + fe80::1/64
eth3            up      default         + fe80::5054:ff:fe73:ed68/64
eth4            up      default         fe80::1/64
eth5            up      default         fe80::1/64
eth6            up      default         fe80::1/64
eth7            up      default         fe80::1/64
lo              up      default         192.168.255.1/32
                                        2001:db8::1/128
```

<br><br>

# FRRのDockerイメージを作る

FRRの公式マニュアルにDockerイメージの作り方が書かれていますので、それに従います。

https://docs.frrouting.org/projects/dev-guide/en/latest/building-docker.html


CMLに適当なUbuntuを作ります。

Dockerをインストールします。

必要なツールをインストールします。

```bash
sudo apt update
sudo apt install ca-certificates curl gnupg
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

dockerグループを作成してciscoアカウントをグループに所属させます。

```bash
sudo groupadd docker
sudo usermod -aG docker cisco
```

docker-engineをインストールします。

```bash
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

FRRのソースコードを取ってきます。

```bash
git clone https://github.com/FRRouting/frr.git
```

移動します。

```bash
cd frr
```

ビルドします。長い時間かかります。

```bash
sudo docker build -t frr-ubuntu22:latest -f docker/ubuntu-ci/Dockerfile .
```

イメージをtar形式でセーブします。

```bash
docker save frr-ubuntu22:latest > frr.tar
```

圧縮します。

```bash
gzip frr.tar
```

アップロードします。

```bash
scp frr.tar.gz admin@192.168.122.212:
```

コックピット側のdropfolderから移動します。

```bash
mv /var/local/virl2/dropfolder/frr.tar.gz /home/admin/
```

イメージ定義ファイルをコピーします。

```bash
cp /var/lib/libvirt/images/virl-base-images/frr-10-2-1-r1/frr-10-2-1-r1.yaml .
```

SHA256を計算します。

```bash
sha256sum frr.tar.gz
```

実行例

```bash
root@cml-controller:~# sha256sum frr.tar.gz
71e2b8fcbf3e2570b2bec387b5b31456aff901cfcc997f1ce2b1dbbef2313afd  frr.tar.gz
```






削除します。

```bash
docker rmi frr-ubuntu22:latest
```
