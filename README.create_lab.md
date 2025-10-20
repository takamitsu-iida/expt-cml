# virl2_clientを使ってラボを作成する

<br>

ノード数が多いラボを作るときには、手作業で作成するよりもPythonで作成した方が圧倒的に簡単です。

<br><br>

## 環境構築

Pythonを使いますので環境を整えます。

direnvをインストールしておくと楽できます。

```bash
sudo apt install direnv
echo "eval \"\$(direnv hook bash)\"" >> ~/.bashrc
source ~/.bashrc```
```

venvを使いますので、インストールします。

```bash
sudo apt install python3-venv
```

このリポジトリをクローンします。

```bash
git clone https://github.com/takamitsu-iida/expt-cml.git
```

移動します。

```bash
cd expt-cml
```

venvをセットアップします。

```bash
python3 -m venv .venv
direnv allow
pip install --upgrade pip
pip install -r requirements.txt
```

<br>

> [!NOTE]
>
> Pythonのモジュール virl2_client はCMLのバージョンと一致させる必要があります。requirements.txtに記載のバージョンを確認してください。

<br>

<br><br>

## CMLに接続するための情報を設定する

virl2_clientは以下の環境変数から接続に必要な情報を読み取ります。

- VIRL2_URL もしくは VIRL_HOST

- VIRL2_USER もしくは VIRL_USERNAME

- VIRL2_PASS もしくは VIRL_PASSWORD

<br>

binディレクトリにあるPythonスクリプトは、
環境変数が設定されてなかった場合、同じ場所にある `cml_env` ファイルから情報を読み取ります。

環境変数を設定するか `cml_env` ファイルを書き換えます。私の環境は以下のように設定されています。

```bash
VIRL_HOST="192.168.122.212"
# or VIRL2_URL

VIRL2_USER="admin"
# or VIRL_USERNAME

VIRL2_PASS="Cisco123"
# or VIRL_PASSWORD
```

<br>

> [!NOTE]
>
> マニュアルから引用。
>
> If no username or password are given then the environment will be checked,
> looking for VIRL2_USER or VIRL_USERNAME and VIRL2_PASS or VIRL_PASSWORD, espectively.
> Environment variables take precedence over those provided in arguments.
>
> It’s also possible to pass the URL as an environment variable VIRL2_URL or VIRL_HOST.

<br><br>

## 事前準備

Pythonスクリプトでラボを作成するにあたって、手作業で簡単なラボを作って、必要な情報を確認します。

使いたいノードを適当に散りばめてラボを作成します。情報確認のために使うだけなのでラボの名前は設定しなくて構いません。

このときノードの設定で `Image Definition` は `Automatic` ではなく手作業で選択します。

<br>

![適当に作成したラボ](./assets/create_lab_1.png)

<br>

上部のメニューから　`LAB`　→　`Download Lab`　を辿ってラボの情報をYAMLでダウンロードします。

抜粋すると、こんな感じです。

`node_definition`　および　`image_definition`　が重要なパラメータで、これらでノードの種類と起動するイメージを識別しています。欲しい情報はこの２つです。

```YAML
nodes:
  -
    label: frr-0
    image_definition: frr-10-2-1-r1
    node_definition: frr
    x: -224
    y: -147

  -
    label: ubuntu-0
    image_definition: ubuntu-24-04-20250503
    node_definition: ubuntu
    tags: []
    x: -71
    y: -86

  -
    label: csr1000v-0
    image_definition: csr1000v-17-03-08a
    node_definition: csr1000v
    tags: []
    x: 114
    y: -93

  -
    label: unmanaged-switch-0
    node_definition: unmanaged_switch
    x: -19
    y: -250

  -
    label: ext-conn-0
    node_definition: external_connector
    x: -17
    y: -418
```

Ubuntuを作りたければ、node_definitionは `ubuntu` を、image_definitionは `ubuntu-24-04-20250503` を指定すればよいことになります。

それさえ分かれば、このラボおよびダウンロードしたYAMLは破棄して構いません。

<br><br>

## ubuntuを含むラボを作ってみる

スクリプト [bin/cml_create_lab1.py](/bin/cml_create_lab1.py) がたたき台となるサンプルです。

Ubuntuイメージはcloud-initで初回起動時に初期化処理を実行します。

よく使う設定を埋め込んでおくと楽できます。


<br><br>

## FRR(Docker)を含むラボを作ってみる

スクリプト [bin/cml_create_lab2.py](/bin/cml_create_lab2.py) がたたき台となるサンプルです。

CML2.9からサポートされたDockerのイメージも同じようにPythonで作れます。

DockerイメージでFRRを動かす場合、設定ファイルが複数ありますので、設定ファイルの名前とその中身を辞書型にして渡してあげる必要があります。

ここがハマりどころです。

```python
# FRRに設定するファイル一式
frr_configurations = [
    {
        'name': 'node.cfg',
        'content': ★ここにnode.cfgの中身を指定
    },
    {
        'name': 'protocols',
        'content': ★ここにprotocolsの中身を指定
    }
]

# FRRノードに設定を適用する
frr_node.configuration = frr_configurations
```
