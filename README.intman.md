
（このページはAdvent Calendar 2025向けに執筆したものです）

（内容はそのうちアップデートします）

# CMLでトラフィック量が分かるようにしてみた

Cisco Modeling Labs (以下CML)はネットワークの分野に関心のある人には必需品と言っても過言ではない、いい製品だと思います。

ただ、使い込んでいくと、不便に感じるところがチラホラと出てくるものです。

私の場合は、検証するネットワーク構成が等コストマルチパスの事が多いので　<span style="font-size: 200%;">通信がどのインタフェースを通っているのか分からない</span>　という問題があります。

パケットをキャプチャして中身を確認するときに等コストマルチパスになっていると、
どっちのインタフェースを通っているのか　<span style="font-size: 200%;">勘で判断するしかない</span>　のですが、だいたいそういうときって外れますね。

ということで、トラフィックがどこを通っているのか、見えるようにしてみました。

<br><br>

## TIG(Telegraf/InfluxDB/Grafana)を使ってみる（失敗）

結果は想像通りです。

CML2.9からDockerをサポートしましたので、
一つのコンテナにTelegraf, InfluxDB, Grafana, SSH, SNMPなどなど、
使えそうなものを全部詰め込んだイメージを作ってみました。

ですが、いかんせん面倒くさいです。

常時使うものならよいのですが、ぱっと立ち上げて、ササッと消しちゃうようなラボ環境で、TIGなんて大げさです。

（最初からわかってたことですが、Dockerイメージを作ってみたかっただけです）


<br><br>

## deadmanを参考にしてみる

Windows環境で複数の宛先にpingを打つときはExPingを使う人が多いと思います。

Linux環境ではdeadmanが便利です。

<br>

![deadman](/assets/deadman-demo.gif)

<br>

この見た目がいいですよね。

[deadman](https://github.com/upa/deadman) はオープンソースですので、
ソースコードを覗いてみると、Pythonのスクリプトだとわかります。

Pythonならある程度理解できますので、改造して使えるかも。

と思ったのですが、中身の解読は難しそうです。

そこでdeadmanのソースコードの一部を流用させていただいて、
もっと簡単なスクリプトを書き起こしてみました。

[deadman.py](bin/deadman.py)

およそ300行くらいのシンプルなスクリプトで再実装できました。

これをたたき台にして、pingのRTTではなく、通信量（PPS）を表示するようにしてみます。

<br><br>

## トラフィック量の取得

Pythonのモジュール virl2_client を使います。

[マニュアル](https://pubhub.devnetcloud.com/media/virl2-client/docs/latest/api/virl2_client.models.html#module-virl2_client.models.interface)を見ると、インタフェースに `readpackets` と `writepackets` というプロパティがあります。

1秒ごとに `readpackets` と `writepackets` を参照して、packet per secondsを計算すれば良さそうです。

<br><br>

## やってみた


<!--
アニメーションGIFの作り方
- Windows + G でゲームBarを起動する
- 動画をキャプチャする
- キャプチャ時間は30秒以内に収める
- ezgif.comでGIFに変換する
-->