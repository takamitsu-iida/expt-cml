# Telegraf/InfluxDB/Grafana

一つのコンテナの中でTIGスタックを動かします。

各サービスはsupervisordで起動します。

コンテナが終了しないように bash -i をループさせます。

<br>

## Dockerイメージ作成

このリポジトリをクローンします。

```bash
git clone https://github.com/takamitsu-iida/expt-cml.git
```

移動します。

```bash
cd expt-cml
```

イメージをビルドします。

```bash
make build
```

コンテナを実行して動作を確認する場合。

```bash
make run
make shell
```

コンテナを停止。

```bash
make stop
```

キャッシュ削除。

```bash
make clean
make prune
```

CMLの/var/tmpにアップロード。

```
make inspect
make save
make upload
```

CMLに登録。

コックピットのターミナルでルート特権を取ってから、

```bash
bash /var/tmp/cml_install_image.sh
systemctl restart virl2.target
```


<br>

## Telegraf動作確認

コンテナの中で直接telegrafを起動して値が取れるかを確認します。

```bash
telegraf --config /etc/telegraf/telegraf.conf --test
```

<br>

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
