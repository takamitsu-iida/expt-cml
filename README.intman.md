
<!--
（このページはAdvent Calendar 2025向けに執筆したものです）

（内容はそのうちアップデートします）
-->

# Cisco CMLでトラフィック量が分かるようにしてみた

Cisco Modeling Labs (以下CML)はネットワークの分野に関心のある人には必需品と言っても過言ではない、いい製品だと思います。

ただ、使い込んでいくと不便に感じるところがチラホラと出てくるものです。

私の場合は、検証するネットワーク構成が等コストマルチパスの事が多いので　**通信がどのインタフェースを通っているのか分からない**　という問題があります。

パケットをキャプチャして中身を確認するときに等コストマルチパスになっていると、
どっちのインタフェースを通っているのか　**勘で判断するしかない**　のですが、だいたいそういうときって外れますね。

ということで、トラフィックがどこを通っているのか、見えるようにしてみました。

<br><br><br>

## TIG(Telegraf/InfluxDB/Grafana)を使ってみる（失敗）

結果は想像通りです。

CML2.9からDockerをサポートしましたので、
一つのコンテナにTelegraf, InfluxDB, Grafana, SSH, SNMPなどなど、
使えそうなものを全部詰め込んだイメージを作ってみました。

これはこれで便利なのですが、通信量を把握するためにこれを起動して設定するのは、いかんせん面倒くさいです。

常時使うものならよいのですが、ぱっと立ち上げて、ササッと消しちゃうようなラボ環境で、TIGなんて大げさです。

（たんにDockerイメージを作ってみたかっただけです）

<br><br><br>

## deadmanを参考にしてみる

Windows環境で複数の宛先にpingを打つときはExPingを使う人が多いと思います。

一方、Linux環境では [deadman](https://github.com/upa/deadman) が便利です。

これです（↓）

<br>

![deadman](/assets/deadman-demo.gif)

<br>

この見た目がいいんですよね！　ターミナルなのにグラフっぽい描画で。

deadmanのソースコードを覗いてみると、Pythonで書かれたスクリプトだとわかります。

Pythonならある程度理解できますので、改造して使えるかも！？　と思ったのですが、中身はちょっと難しく・・・

そこでdeadmanの見た目表示のアイデアを流用させていただいて、もっと簡単なスクリプトを書き起こしてみました。

[deadman.py](bin/deadman.py)

およそ300行のシンプルなスクリプトで再実装できました。

これをたたき台にして、pingのRTTではなく、通信量（PPS）を表示するようにしてみます。

<br><br>

## CMLのトラフィック量はどうやって取得する？

CMLのラボの中を流れるトラフィックの量を把握するために、Pythonのモジュール virl2_client を使います。

virl2_clientのマニュアルを見ると、インタフェースに `readpackets` と `writepackets` というプロパティがあります。

定期的に `readpackets` と `writepackets` を参照して、packet per secondsを計算すればトラフィック量は把握できそうです。

<br>

> [!NOTE]
>
> マニュアルはこちら。
>
> https://pubhub.devnetcloud.com/media/virl2-client/docs/latest/api/virl2_client.models.html#module-virl2_client.models.interface


<br><br>

## 早速やってみた

作成したスクリプトは [intman.py](/bin/intman.py) です。使い方はスクリプト内に書いてあります。

デモ用に簡単なラボで試してみます。

<br>

![demo](/assets/intman-lab.png)

<br>

R1とR2はCSR1000vです。

等コストマルチパスになっていますので、R1からR2へのICMP RequestはGig1かGig2のどちらかを通ります。
戻って来るICMP Responseもどっちで受信するかは分かりません。

ターミナルを２つ開いて、一方で `intman.py` を実行、もう一方でpingを打ってみます。

見た目はこのようになります。

<br>

![intman](/assets/intman.gif)

<br>

今回の場合、R1 と R2 共にGig2で送受信しているのが分かります。

また、打ち込んでいる連続pingの量でバーの高さが変わりますので、トラフィックの量が多いか少ないか、がなんとなくわかります。

実際に何ppsだったのか、までは表示していませんが、どのインタフェースを通過しているかを把握するにはこの程度で十分です。

<br><br><br>

# まとめ

Pythonのモジュール virl2_client を使ってCMLの中を流れるトラフィック量を手っ取り早く可視化しました。

ちゃんとしたGUIアプリを作ろうとすると大変ですが、ターミナルで動く軽量なモノであれば意外と簡単にできるものです。

[deadman.py](/bin/deadman.py) と [intman.py](/bin/intman.py) はどちらも短いPythonスクリプトですので、
ぜひ改造して使ってみてください。

PPSじゃなくてBPS(Bit Per Second)の方がいいな、くらいなら、あっという間に改造できちゃうと思いますし、
他にも過去の履歴を残しながら状態を表示したい、みたいな場面でいろいろ応用できると思います。


<br><br><br><br><br><br>

<br>

> [!NOTE]
>
> [cml_create_intman_demo.py](bin/cml_create_intman_demo.py) を実行すると、intman.pyを動かすラボ環境が整います。

<br>

> [!NOTE]
>
> CMLでUbuntuを作成した場合、環境変数の設定が原因でcursesアプリは動きません。
>
> 以下を試してください。
>
> ```bash
> export LC_ALL="en_US.UTF-8"
> export TERM="linux"
> ```

<br>

> [!NOTE]
>
> virl2_clientのソースコード `interface.py` をみると、
> readpacketsやwritepacketsといった統計値はある程度時間が経過してたら更新して、そうでなければ現在持っている値を返却します。
>
> ```python
>   @property
>   def readpackets(self) -> int:
>       """Return the number of packets read by the interface."""
>       self.node._lab.sync_statistics_if_outdated()
>       return int(self.statistics["readpackets"])
> ```
>
> `node.py` をみると、自動更新が有効、かつ現在時刻と前回取得したときの時刻の差分が self._lab.auto_sync_interval よりも大きいときだけ更新します。
>
> ```python
>   def sync_interface_operational_if_outdated(self) -> None:
>       timestamp = time.time()
>       if (
>           self._lab.auto_sync
>           and timestamp - self._last_sync_interface_operational_time
>           > self._lab.auto_sync_interval
>       ):
>           self.sync_interface_operational()
> ```
>
> `lab.py` をみると、このように初期化されてますので、1.0秒以上経過していたら取りに行く、という動作をしています。
>
> ```python
>   def __init__(
>       self,
>       title: str | None,
>       lab_id: str,
>       session: httpx.Client,
>       username: str,
>       password: str,
>       auto_sync: bool = True,
>       auto_sync_interval: float = 1.0,
>       wait: bool = True,
>       wait_max_iterations: int = 500,
>       wait_time: int | float = 5,
>       hostname: str | None = None,
>       resource_pool_manager: ResourcePoolManagement | None = None,
>   ) -> None:
> ```
>
> ということは、トラフィック量を測定するインターバルも1秒（よりも僅かに長い時間）に合わせておくと良さそうです。
