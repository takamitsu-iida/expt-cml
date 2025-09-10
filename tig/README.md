# TIG


## 動作確認

influxdbに値があるかどうか

```bash
influx query '
from(bucket: "my_bucket")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "cpu")
  |> limit(n:5)
' --org my_org --token $TOKEN --host http://localhost:8086
```
