# ターミナル関連のあれこれ

CMLでPATtyを有効にすると、CML外部からのtelnet接続でラボ内の機器のコンソールを開けますので、とても便利です。

TeraTERMやPuTTY等、使い慣れたターミナルがある方はそれを使えばよいと思いますが、私はWSLと相性のよいWindows Terminalを愛用しています。

`telnet 192.168.122.212 5001` とか、もう何度実行したか分からないくらい手打ちしているわけですが、
さすがにそろそろ効率化しようかな、と思います。

<br><br>

## WindowsのhostsファイルにCMLのアドレスを登録する

Windowsのhostsファイルに記載することでWSL側でも名前解決できるようになります。

hostsファイルの場所は `C:\windows\system32\drivers\etc` です。

この場所は通常のユーザは書き込めませんので、コマンドプロンプトを管理者モードで起動してから、メモ帳を起動して編集します。

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

GUIで設定してもいいですが、JSONを直接書いた方が簡単です。

＜画像を入れる＞


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
...
```

- "commandline" に実行するコマンドを入れます。WSL(Ubuntu)にインストールされているtelnetを起動します。

- "hidden" は常にfalseを指定します。

- "name" は短い方がよく、またスペースを含めないほうがいいです。

なお "guid" は必須のパラメータですが、Windows Terminalが勝手に割り当てるので、自分で書く必要はありません。

<br>

> [!NOTE]
> "commandline" にtelnet.exeを書いてもいいのですが、telnet.exeの改行コードはCRLFになっていてルータとの相性が悪いです。
> WSL(Ubuntu)にtelnetを入れて、それを起動した方が快適です。

<br>

この設定が反映されると Windows Terminal のGUI操作で直接telnetできるようになります。

＜GIFアニメを入れる＞

<br><br>

## 複数のルータのターミナルを一度に開く

ラボ内にルータが複数あるときに、それごとにターミナルを開くのは面倒です。

Windows Terminalを開いて、ペインに分割して開くbashスクリプト [open_terminal.sh](/bin/open_terminal.sh) を作成しました。

Windows Terminalのペイン分割は挙動が複雑なので、思ったよりも難しかったです。

引数に上記の "name" で指定したアクション名を渡してあげると、それがペインとして開きます。

```bash
bin/open_terminal.sh t5001 t5002 t5003
```
