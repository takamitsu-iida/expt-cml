# TIG

## Telegraf動作確認

```bash
telegraf --config /etc/telegraf/telegraf.conf --test
```

## 動作確認

influxdbに値があるかどうか

```bash
influx query '
from(bucket: "my_bucket")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "cpu")
  |> limit(n:5)
' --org $DOCKER_INFLUXDB_INIT_ORG --token $DOCKER_INFLUXDB_INIT_ADMIN_TOKEN --host http://localhost:8086
```
