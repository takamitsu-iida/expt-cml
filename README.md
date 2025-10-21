<br>

## CMLのインストール

Windows11のHyper-Vの上にCMLを入れています。いまのところこの構成が一番いいように思います。

[README.install_cml.md](/README.install_cml.md)

<br>

## ラボ内の装置に接続するターミナル操作

Windows Terminal使いの方にオススメしたい使い方です。

[README.terminal.md](/README.terminal.md)

<br>

## Python virl2_clientを使ったラボの作り方

手作業でラボを作るよりも、Pythonスクリプトで作った方が圧倒的に楽です。

[README.create_lab.md](/README.create_lab.md)

<br>

## Ubuntuのカスタムイメージの作り方

Ubuntuはよく使うので、自分用にカスタマイズしたものを用意した方が便利です。

[README.create_custom_ubuntu.md](/README.create_custom_ubuntu.md)

<br>

## FRRをインストールしたUbuntuの作り方

Ubuntuのカスタムイメージの作り方は大事なので記録として残していますが、**実用上はDockerがオススメ**です。

[README.create_custom_ubuntu_frr.md](/README.create_custom_ubuntu_frr.md)

<br>

## FRRをインストールしたUbuntuでOpenFabricを検証

FRRをコンパイルして作成する方法は大事なので記録として残していますが、**実用上はDockerがオススメ**です。

[README.openfabric_ubuntu.md](/README.openfabric_ubuntu.md)

<br><br><br>

## Dockerイメージの作り方

CML2.9からDockerをサポートしています。Ubuntuをベースにして、よく使うパッケージを詰め込んだDockerイメージを作成してみます。

[README.create_custom_docker.md](/README.create_custom_docker.md)

<br>

## TIG(Docker)の作り方

Telegraf/InfluxDB/Grafanaを詰め込んだコンテナイメージを作ります。

[README.tig_docker.md](/README.tig_docker.md)

<br>

## FRR(Docker)イメージの作り方

FRRを使うときはVRFやIPv6中継も必要になることが多いです。CMLのDockerではノード定義ファイルでsysctlを設定します。

[README.create_frr_docker.md](/README.create_frr_docker.md)

<br>

## FRR(Docker)でOpenFabricを検証

合計13台のFRR(Docker)を使ってOpenFabricのルーティング動作を検証します。

[README.openfabric_docker.md](/README.openfabric_docker.md)

<br>

## FRR(Docker)でSRv6 L3VPNを検証

Pルータ2台、PEルータ4台、CEルータ4台の合計10台のFRR(Docker)を使ってSRv6の動作を検証します。

[README.srv6_docker.md](/README.srv6_docker.md)

<br><br><br>

## Visual Studio CodeからMCPでラボを操作

Github Copilotのエージェントモードを使ってCMLのラボを操作します。

[README.mcp.md](/README.mcp.md)


<!--
アニメーションGIFの作り方
- Windows + G でゲームBarを起動する
- 動画をキャプチャする
- キャプチャ時間は30秒以内に収める
- ブラウザで ezgif.com を開く
- Video to GIF を開く
- アップロードして変換する
-->