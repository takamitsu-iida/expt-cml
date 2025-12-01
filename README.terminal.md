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

## キーバインドを修正する

Cisco IOSではコマンドの中止を `ctrl+shift+6` に割り当てています。

Windows Terminalもデフォルトで同じキーバインドを割り当てていますので、これを削除します。

GUIで「設定 → 操作」の順に辿ります。

![delete keybind](/assets/windows_terminal_key_bind.png)

<br><br>

## 複数のアクションプロファイルを一度に開く

CMLのラボを起動したり、停止したり、といった作業はVisual Studio CodeでPythonスクリプトを書いて実行していますので、
できることならWindows Terminalの起動もVSCodeのターミナルからコマンドで起動したいところです。

WVS(Ubuntu)の中にいてもWindows Terminalを起動するwt.exeを実行できますので、
このように起動すればアクションプロファイルで指定した接続先につながります。

```bash
wt.exe -p t5001
```

<br>

ラボ内にルータが複数あるときに、それごとにWindows Terminalを開くのは面倒ですし、なによりウィンドウがたくさんあるのって嫌ですよね。

そこで、Windows Terminalをペインに分割して一気に開くbashスクリプト [open_profile.sh](/bin/open_profile.sh) を作成しました。

作成済みのWindows Terminalのアクションプロファイルを指定して、次のように実行します。

**例１．プロファイルが一つの場合**

普通にWindows Terminalが起動します。

```bash
bin/open_profile.sh t5011
```

![t5011](/assets/windows_terminal_t5011.png)

<br><br>

**例２．プロファイルが２つの場合**

左右に分割した状態で起動します。

```bash
bin/open_profile.sh t5011 t5012
```

![t5011 t5012](/assets/windows_terminal_t5011_t5012.png)

<br><br>

**例３．プロファイル３個の場合**

左側に２個のペイン、右側に１個のペインの構成で起動します。

```bash
bin/open_profile.sh t5011 t5012 t5013
```

![t5011 t5012 t5013](/assets/windows_terminal_t5011_t5012_t5013.png)

<br><br>

**例４．プロファイル４個の場合**

左側に２個のペイン、右側に２個のペインの構成で起動します。

```bash
bin/open_profile.sh t5011 t5012 t5013 t5014
```

![t5011 t5012 t5013 t5014](/assets/windows_terminal_t5011_t5012_t5013_t5014.png)

<br>

左右2分割して、必要なだけ上下に分割して開きます。

特に上限は設けていませんが、実用上は6個くらいかな、と思います。

<br><br>

## ポート番号を指定して同時に開きたい場合

PATtyで接続したい装置のポート番号を列挙して、コマンド一発でターミナルを開くbashスクリプト [open_terminal.sh](bin/open_terminal.sh) を作りました。

アクションプロファイルを作らなくて良いので、こっちの方が便利かもしれません。

<br>

> [!NOTE]
>
> CMLのIPアドレスはホスト名 `cml` で名前解決していますので、
> hostsファイルを作成していない場合はスクリプトを書き換えてIPアドレスを直書きしてください。

<!-- TODO: VIRL2_HOSTのような環境変数からCMLのアドレスを得ること -->

<br>

> [!NOTE]
>
> ログを取る機能を追加したら、綺麗に4分割されないケースが出てしまいました（泣）
>
> telnetコマンドの前にscriptを入れただけなのですが・・・

<br>

開きたいポートが5011と5012の場合、WVS(Ubuntu)のターミナルからこのように実行します。

```bash
bin/open_terminal.sh 5011 5012
```

接続先ポート番号を2個以上指定した場合はペインに分割して開きます。

<br><br>

## 全てのペインに同じコマンドを送る

Windows Terminalのコマンドパレットに「**ブロードキャスト入力をすべてのウィンドウに切り替える**」というのがあります。

分かりづらい日本語ですが、ペインに分割した状態でキーボードを叩いたときに、キー入力をすべてのペインに送信する機能です。

Ctrl-Shift-Pでコマンドパレットを開いて「ブロードキャスト」と日本語で入れてリターンです。

トグルなので、止めたいときも同じ操作です。

<br>

![broadcast](/assets/windows_terminal_broadcast_input.gif)

<br>

左右にペインを並べた状態で show running-config を実行すれば、設定を見比べることができてとても便利です。
