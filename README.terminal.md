# ターミナル関連のあれこれ

CMLでPATtyを有効にすると、CML外部からのtelnet接続でラボ内の機器のコンソールを開けますので、とても便利です。

TeraTERMやPuTTY等、使い慣れたターミナルがある方はそれらでtelnetすればいいと思いますが、
私はWSLと相性のよいWindows Terminalを愛用していまして、毎回 `telnet 192.168.122.212 5001` というように手打ちしてます。

さすがにそろそろ効率化しようかな、と思います。

<br><br>

## IPアドレスを手打ちしないためのWindows hostsファイル設定

まずはCMLのIPアドレスを手打ちしなくていいようにします。

Windowsのhostsファイルに記載することでWSL側でも名前解決できるようになります。

hostsファイルの場所は `C:\windows\system32\drivers\etc` です。

この場所は通常のユーザは書き込めませんので、**コマンドプロンプトを管理者モードで起動して**から、メモ帳で編集します。

```bash
notepad c:\windows\system32\drivers\etc\hosts
```

CMLのIPアドレスを記載しておきます。

```text
192.168.122.212 cml
```

これでWindows、WSL(Ubuntu)共に `cml` というホスト名でアクセスできるようになります。

<br><br>

## telnetコマンドを手打ちしないためのWindows Terminal設定

Windows Terminalの設定を開きます。

GUIで設定してもいいですが、JSONで直接書いた方が簡単です。

<br>

![windows terminal config](/assets/windows_terminal_setting.png)

<br>

"profiles" の配列に次のような設定を入れておきます。

<br>

```json
{
    "commandline": "wsl -e /usr/bin/telnet cml 5001",
    "hidden": false,
    "name": "t5001"
},
{
    "commandline": "wsl -e /usr/bin/telnet cml 5002",
    "hidden": false,
    "name": "t5002"
},
{
    "commandline": "wsl -e /usr/bin/telnet cml 5003",
    "hidden": false,
    "name": "t5003"
},

```

- "commandline" に実行するコマンドを入れます。WSL(Ubuntu)にインストールされている/usr/bin/telnetを起動します。

- "hidden" は常にfalseを指定します。

- "name" は短い方がよく、またスペースを含めないほうがいいです。

なお "guid" は必須のパラメータですが、Windows Terminalが勝手に割り当てるので自分で書く必要はありません。

<br>

> [!NOTE]
>
> "commandline" にtelnet.exeを書いてもいいのですが、telnet.exeの改行コードはCRLFになっていてルータとの相性が悪いです。
>
> WSL(Ubuntu)のtelnetを起動した方が快適です。

<br>

この設定が反映されると Windows Terminal のGUI操作だけでルータに接続できるようになります。

Windows Terminalの下向き矢印を押すと登録したアクションプロファイルが出てきますので、それを選択するだけです。

<br>

![open tab](/assets/windows_terminal_open_tab.gif)

<br><br>

## 複数のアクションプロファイルを一度に開く

ラボ内にルータが複数あるときに、それごとにターミナルを開くのは面倒です。

Windows Terminalをペインに分割して開くbashスクリプトを作成しました。

すでにWindows Terminalのアクションプロファイルを作成済みであれば、その名前を指定して開きます。

<br>

> [!NOTE]
>
> Windows Terminalのペイン分割は挙動が複雑なので、思ったよりもスクリプトは難しかったです。
>
> ソースコードはこちら。
>
> [open_profile.sh](/bin/open_profile.sh)

<br>

スクリプトの引数に上記の "name" で指定したアクションプロファイル名を渡してあげると、それがペインとして開きます。

例１．プロファイルが一つの場合

普通にWindows Terminalが起動します。

```bash
bin/open_profile.sh t5011
```

![t5011](/assets/windows_terminal_t5011.png)

<br>

例２．プロファイルが２つの場合

左右に分割した状態で起動します。

```bash
bin/open_profile.sh t5011 t5012
```

![t5011 t5012](/assets/windows_terminal_t5011_t5012.png)

<br>

例３．プロファイル３個の場合

左側に２個のペイン、右側に１個のペインの構成で起動します。

```bash
bin/open_profile.sh t5011 t5012 t5013
```

![t5011 t5012 t5013](/assets/windows_terminal_t5011_t5012_t5013.png)

<br>

例４．プロファイル４個の場合

左側に２個のペイン、右側に２個のペインの構成で起動します。

```bash
bin/open_profile.sh t5011 t5012 t5013 t5014
```

![t5011 t5012 t5013 t5014](/assets/windows_terminal_t5011_t5012_t5013_t5014.png)


<br><br>

## プロファイルを作っていないけど同時に開きたい場合

アクションプロファイルを作るのって、それはそれで面倒です。

bashのスクリプトに開きたいtelnetのポート番号を記述しておいて、コマンド一発でターミナルを開くこともできます。

<br>

> [!NOTE]
>
> ソースコードはこちら。接続先ごとにコピーして使うといいと思います。
>
> [open_terminal.sh](/bin/open_terminal.sh)

<br>

開きたいポートが5011と5012の場合、open_terminal.shにはこのように記述します。

```bash
# CMLのIPアドレス
CML="192.168.122.212"

# PATtyで接続したいポート番号
# PORT_LIST=(5011)
PORT_LIST=(5011 5012)
# PORT_LIST=(5011 5012 5013)
# PORT_LIST=(5011 5012 5013 5014)
```

接続先ポート番号が2個以上ある場合はペインに分割して開きます。

<br><br>

## 全てのペインに同じコマンドを送る

Windows Terminalのコマンドパレットに「**ブロードキャスト入力をすべてのウィンドウに切り替える**」というのがあります。

分かりづらい日本語ですが、ペインに分割した状態でキー入力をすべてのペインに送信する機能です。

Ctrl-Shift-Pでコマンドパレットを開いて「ブロードキャスト」と日本語で入れてリターンです。

トグルなので、止めたいときも同じ操作です。

<br>

![broadcast](/assets/windows_terminal_broadcast_input.gif)

<br>