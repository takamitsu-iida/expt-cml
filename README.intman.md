
<!--
（このページはAdvent Calendar 2025向けに執筆したものです）

（内容はそのうちアップデートします）
-->

# Cisco CMLでトラフィック量が分かるようにしてみた

<br>

Cisco Modeling Labs (以下CML)はネットワークの分野に関心のある人には必需品と言っても過言ではない、いい製品だと思います。

ただ、使い込んでいくと不便に感じるところがチラホラと出てくるものです。

私の場合は、検証するネットワーク構成がイコールコストマルチパス(ECMP)になる事が多いので　**通信がどのインタフェースを通っているのか分からない**　という困りごとがあります。

パケットをキャプチャして中身を確認するときにECMPになっていると、
どっちのインタフェースを通っているのか　**勘で判断するしかない**　のですが、だいたいそういうときって外れますね。

ということで、トラフィックがどこを通っているのか、見えるようにしてみました。

<br><br><br>

## TIG(Telegraf/InfluxDB/Grafana)を使ってみる（失敗）

結果は想像通りです。

CML2.9からDockerをサポートしましたので、
一つのコンテナにTelegraf, InfluxDB, Grafana, SSH, SNMPなどなど、
使えそうなものを全部詰め込んだイメージを作ってみました。

Grafanaで綺麗なグラフが出るとそれだけで嬉しいですが、
通信量を把握するためにこれを起動して設定するのは、いかんせん面倒くさいです。

常時使うものならよいのですが、ぱっと立ち上げて、ササッと消しちゃうようなラボ環境で、TIGなんて大げさです。

（たんにDockerイメージを作って遊んでみたかっただけです。使ってみたい方は[こちら](/README.tig.md)をどうぞ）

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

CMLのラボの中を流れるトラフィック（パケット）の統計値はどこかしらに記録されているはずです。

CMLが使っているハイパーバイザはKVMなので、コマンドを駆使すれば取得できそうですが、ラボの中のどのインタフェースがKVMのどれに相当するのか、対応付けるのがめんどくさそうです。

何かいい方法はないかな～、とPythonのモジュール virl2_client のマニュアルを眺めてみますと、
インタフェースに `readpackets` と `writepackets` というプロパティがありました。

定期的に `readpackets` と `writepackets` を参照して、packet per secondsを計算すればトラフィック量は把握できそうです。

<br>

> [!NOTE]
>
> readpacketsおよびwritepacketsプロパティのマニュアルはこちらを参照。
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

イコールコストマルチパスになっていますので、R1からR2へのICMP RequestはGig1かGig2のどちらかを通ります。
戻って来るICMP Responseもどっちで受信するかは分かりません。

ターミナルを２つ開いて、一方で `intman.py` を実行、もう一方でpingを打ってみます。

見た目はこのようになります。

<br>

![intman](/assets/intman.gif)

<br>

今回の場合、R1 と R2 共にGig2で送受信しているのが分かります。

また、打ち込んでいる連続pingの量でバーの高さが変わりますので、トラフィックの量が多いか少ないか、がなんとなくわかります。

実際に何pps出てるのかはわかりませんが、どのインタフェースを通過しているかを把握するにはこの程度で十分です。

<br><br>

今度はもうちょっと実践的なラボ、[SRv6を使ったL3VPN](/README.srv6.md)の構成で試してみます。

PEルータとPルータはSRv6網を構成しています。
CEルータ間の通信は、入口のPEルータでSRv6にカプセル化されて、出口のPEルータで元のIPパケットの戻ります。
SRv6網内はECMPになっていて、行き・帰りの通信は共にどこを通るか予測できません。

![srv6-lab](/assets/srv6_docker_lab.png)

<br>

Visual Studio Codeのターミナルを2分割して、一方でintman.pyを実行、一方でpingを打ち込んでみます。

<br>

![srv6](/assets/intman-srv6-lab.gif)

<br>

intman.pyの結果から、どのルータの、どのインタフェースにトラフィックが通っているか、なんとなくわかります。

これを絵にするとこんな感じです。

<br>

![ping](/assets/intman-srv6-ping.png)

<br>

行きと帰りは違うところを通ってます。

パケットをキャプチャする場合、闇雲に勘で場所を決めるのではなく、狙った場所でキャプチャできますね！

<br><br>

なお　「**tracerouteすればどこを通ってるか分かるじゃん**」 って言われそうですが、
SRv6のL3VPNだと網内は見えなくて、CEルータ間は1ホップでたどり着いちゃうんです。

```bash
CE101#traceroute 10.0.14.104
Type escape sequence to abort.
Tracing the route to 10.0.14.104
VRF info: (vrf in name/id, vrf out name/id)
  1 10.0.14.1 1 msec 1 msec 1 msec
  2 10.0.14.104 0 msec 0 msec 0 msec
```

<br><br><br>

# まとめ

Pythonのモジュール virl2_client を使ってCMLの中を流れるトラフィック量を手っ取り早く可視化しました。

ちゃんとしたGUIアプリを作ろうとすると大変ですが、ターミナルで動く軽量なモノであれば意外と簡単にできるものです。

[deadman.py](/bin/deadman.py) と [intman.py](/bin/intman.py) はどちらも短いPythonスクリプトですので、
ぜひ改造して使ってみてください。

<br><br><br><br><br><br><br><br>

---

<br>

> [!NOTE]
>
> [cml_create_intman_demo.py](bin/cml_create_intman_demo.py) を実行すると、intman.pyを動かすラボ環境が整います。
>
> ルータ2台とUbuntuが一つ作られます。
>
> Ubuntuは起動時にこのリポジトリをクローンして、必要なものを諸々インストールしますので、以下を実行するだけで環境は整います。
>
> ```bash
> cd expt-cml
> direnv allow
> ```
>
> CMLに接続するためのアカウント情報を bin/cml_env に書いてください。
>
> `bin/intman.py intman.yaml` で実行できます。

<br><br>

> [!NOTE]
>
> CMLの中にUbuntuを作成した場合、そのままだと環境変数の設定が原因でcursesアプリは動きません。
>
> 以下を試してください。
>
> ```bash
> export LC_ALL="en_US.UTF-8"
> export TERM="linux"
> ```
>
> [cml_create_intman_demo.py](bin/cml_create_intman_demo.py) で作成したラボは対策済みですので問題ありません。

<br><br>

> [!NOTE]
>
> virl2_clientのソースコードをみるとreadpacketsやwritepacketsといった統計値は1秒より経過してたら値を更新して、そうでなければ持っている値を返却します。
>
> ということは、トラフィック量を測定するインターバルも1秒（よりも僅かに長い時間）に合わせておくと良さそうです。
