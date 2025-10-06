# Telegraf/InfluxDB/Grafana

一つのコンテナの中でTIGスタックを動かします。

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

イメージをビルドします。時間かかります。

```bash
make build
```

ビルドできたら、コンテナを実行してみます。

```bash
make run
```

コンテナにシェルで接続して動作状況を確認してみます。

```bash
make shell
```

telegraf, influxdb, grafanaすべてのプロセスが起動していれば、ひとまず問題ありません。

動作が確認できたら実行したコンテナを停止します。

```bash
make stop
```

ビルドを繰り返すときは、Dockerのキャッシュを削除してからビルドします。

```bash
make clean
make prune
make build
```

ビルドしたコンテナイメージとノード定義ファイル、イメージ定義ファイルをCMLの/var/tmpにアップロードします。

```
make inspect
make save
make upload
```

CMLに登録します。

この作業は手打ちすると面倒なので、CMLのコックピットのターミナルでルート特権を取ってから、シェルスクリプトを実行します。

```bash
bash /var/tmp/cml_install_image.sh
```

最後にvirl2サービスを再起動します。

```bash
systemctl restart virl2.target
```

<br><br><br>

## Telegrafの動作確認

コンテナの中で直接telegrafを起動して値が取れるかを確認します。

```bash
telegraf --config /etc/telegraf/telegraf.conf --test
```

<br>

## Telegrafの再起動

/etc/telegraf/telegraf.confを変更した場合、サービスを再起動します。

サービスはsupervisord経由で起動していますので、次のようにします。

```bash
supervisorctl restart telegraf
```

<br><br><br>

## InfluxDB動作確認

influxdbに値が蓄積されているか、確認します。

<br>

DockerコンテナのCPU使用率

```bash
influx query '
from(bucket: "my_bucket")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "cpu")
  |> limit(n:5)
' --org $DOCKER_INFLUXDB_INIT_ORG --token $DOCKER_INFLUXDB_INIT_ADMIN_TOKEN --host http://localhost:8086
```

<br>

インタフェースの統計値

```bash
influx query '
from(bucket: "my_bucket")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "interface")
  |> limit(n:5)
' --org $DOCKER_INFLUXDB_INIT_ORG --token $DOCKER_INFLUXDB_INIT_ADMIN_TOKEN --host http://localhost:8086
```

<br>

Telegrafがルータから情報を取得している場合、

```influx
from(bucket: "my_bucket")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "interface" and r._field == "ifHCInOctets")
  |> filter(fn: (r) => r.hostname == "R1" or r.hostname == "R2")
  |> filter(fn: (r) => r.ifDescr == "Ethernet0/0" or r.ifDescr == "Ethernet0/1")
  |> derivative(unit: 1s, nonNegative: true)
  |> map(fn: (r) => ({ r with _value: r._value * 8.0 })) // bpsに変換
```

<br>

## InfluxDBブラウザ

Windows母艦からブラウザで接続します。

http://192.168.0.110:8086


<br>

## Grafanaブラウザ

Windows母艦からブラウザで接続します。

http://192.168.0.110:3000


InfluxDBのトークンはmake build時に生成して環境変数TOKENに保存しています。

make buildを実行したUbuntuであれば、Dockerイメージをインスペクトすれば値は見えます。

```bash
docker images
docker inspect tig:latest
```

すでにCMLに登録してコンテナとして起動済みであれば、コンテナを起動してコンソールから環境変数TOKENを表示します。

```bash
printenv TOKEN
```

GrafanaからInfluxDBを参照する際にこの文字列が必要になりますのでコピーしておきます。

新しいダッシュボードを作ります。

「Add Visualization」をクリックします。

初期状態ではデータソースの設定がないので `Configure a new data source` をクリックします。

- Query languageは Flux に変更します（InfluxDB Detailsの入力内容が変わります）
- HTTP のURLは http://127.0.0.1:8086
- Authはそのままにしておきます（認証不要）
- InfluxDB Details - Organizationに my_org を入力します
- InfluxDB Details - Tokenはコピーしておいたものを貼り付けます
- InfluxDB Details - Default Bucketは my_bucket を入力します

最下部のボタン「Save & test」をクリックして動作を確認します。

Home 画面に戻って「+ Create dashboard」をクリックします。

「Add Visualization」をクリックします。

Select data sourceの部分に登録したinfluxdbがあるのでそれをクリックします。

R1のEthernet0/0の送受信量をクエリします。

```influx
// 受信量
rx = from(bucket: "my_bucket")
  |> range(start: -1h)
  |> filter(fn: (r) => r.hostname == "R1")
  |> filter(fn: (r) => r.ifDescr == "Ethernet0/0")
  |> filter(fn: (r) => r._measurement == "interface" and r._field == "ifHCInOctets")
  |> filter(fn: (r) => exists r._value)
  |> map(fn: (r) => ({ r with _value: float(v: r._value) }))  // 型をfloatに統一
  |> derivative(unit: 1s, nonNegative: true)
  |> map(fn: (r) => ({ r with _value: r._value * 8.0 })) // bpsに変換
  |> set(key: "direction", value: "RX")

// 送信量
tx = from(bucket: "my_bucket")
  |> range(start: -1h)
  |> filter(fn: (r) => r.hostname == "R1")
  |> filter(fn: (r) => r.ifDescr == "Ethernet0/0")
  |> filter(fn: (r) => r._measurement == "interface" and r._field == "ifHCOutOctets")
  |> filter(fn: (r) => exists r._value)
  |> map(fn: (r) => ({ r with _value: float(v: r._value) }))  // 型をfloatに統一
  |> derivative(unit: 1s, nonNegative: true)
  |> map(fn: (r) => ({ r with _value: r._value * 8.0 })) // bpsに変換
  |> set(key: "direction", value: "TX")

union(tables: [rx, tx])
```

これをグラフにします。
