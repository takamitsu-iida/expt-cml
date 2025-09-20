# Telegraf/InfluxDB/Grafana

一つのコンテナの中でTIGスタックを動かします。

各サービスはsupervisordで起動します。

コンテナが終了しないように bash -i をループさせます。

<br>

### 事前準備１．CMLでSSHサーバを有効にする

OpenSSHを有効にしていない場合のみ、コックピットで有効にしてください。ラジオボタンを有効にするだけです。

CMLのSSHサーバはポート1122で待ち受けています（ポート22はコンソールサーバになっています）。

<br>

## 事前準備２．DockerエンジンがインストールされたUbuntuを作成する

Dockerエンジンがインストールされた外部接続できるUbuntuが必要です。

適当に手作業でラボを作ってもいいですが、それなりに面倒なので、[このスクリプト](/bin/cml_create_custom_docker.py)で自動生成します。

初回起動時はcloud-initでアップデートしますのでUbuntuの立ち上げに時間かかります。

<br>

### 事前準備３．SSHの公開鍵を送り込んでおく

DockerエンジンがインストールされたUbuntuにログインします。

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

これでパスワードなしでCMLにログインできるようになります。

<br>

## Dockerイメージを構築

Ubuntuにログインしたら、このリポジトリをクローンします。

```bash
git clone https://github.com/takamitsu-iida/expt-cml.git
```

tigディレクトリに移動します。

```bash
cd expt-cml
cd tig
```

イメージをビルドします。

```bash
make build
```

コンテナを実行して動作を確認してみます。

```bash
make run
make shell
```

実行したコンテナを停止します。

```bash
make stop
```

ビルドを繰り返すときは、Dockerのキャッシュを削除します。

```bash
make clean
make prune
```

CMLの/var/tmpにイメージをアップロードします。

```
make inspect
make save
make upload
```

CMLに登録します。

CMLのコックピットのターミナルでルート特権を取ってから、シェルスクリプトを実行します。

```bash
bash /var/tmp/cml_install_image.sh
systemctl restart virl2.target
```

<br><br><br>

## Telegraf動作確認

コンテナの中で直接telegrafを起動して値が取れるかを確認します。

```bash
telegraf --config /etc/telegraf/telegraf.conf --test
```

<br>

## Telegrafの再起動

/etc/telegraf/telegraf.confを変更したら再起動します。

```bash
supervisorctl restart telegraf
```

<br><br><br>

## InfluxDB動作確認

influxdbに値があるかどうかを確認します。

```bash
influx query '
from(bucket: "my_bucket")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "cpu")
  |> limit(n:5)
' --org $DOCKER_INFLUXDB_INIT_ORG --token $DOCKER_INFLUXDB_INIT_ADMIN_TOKEN --host http://localhost:8086
```

<br>

受信 ifHCInOctets

```influx
from(bucket: "my_bucket")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "interface" and r._field == "ifHCInOctets")
  |> filter(fn: (r) => r["hostname"] == "対象装置のホスト名")
  |> group(columns: ["ifDescr"])
  |> derivative(unit: 1s, nonNegative: true)
```

送信 ifHCOutOctets

```influx
from(bucket: "my_bucket")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "interface" and r._field == "ifHCOutOctets")
  |> filter(fn: (r) => r["hostname"] == "対象装置のホスト名")
  |> group(columns: ["ifDescr"])
  |> derivative(unit: 1s, nonNegative: true)
```

```influx
from(bucket: "my_bucket")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "interface" and r.ifDescr == "GigabitEthernet0/1")
```

<br>

## InfluxDBブラウザ

Windows母艦から、

http://192.168.0.110:8086


<br>

## Grafanaブラウザ

Windows母艦から、

http://192.168.0.110:3000


InfluxDBのトークンはmake build時に生成して、環境変数TOKENに保存しています。

CMLのコンソールでトークンを確認します。

```bash
printenv TOKEN
```

この値をコピーしておいて、Grafanaのデータソースの設定時に使います。
