# MCPメモ

PythonでMCPサーバを作成して、Visual Studio CodeのCopilotで利用できるようにします。

<br>

> [!NOTE]
>
> Copilotの契約によってはvscodeでのMCP利用に制限がかかっていることがあります。
>
> ![vscode](/assets/mcp_vscode_organization.png)

<br><br>

## Visual Studio CodeでMCPを使う

独自のMCPサーバを使うには、vscodeに設定が必要です。

ここではワークスペースの中だけで利用できるように設定します。

`.vscode` ディレクトリを作成します。

```bash
mkdir -p .vscode
```

新しいファイル `mcp.json` を作成します。

エディタの右下に「サーバの追加」というボタンが登場するので、それをクリックします。

vscodeが一気に補完してくれますので、必要な部分を変更します。

<br>

![vscode](/assets/mcp_vscode_workspace.gif)

<br>

```json
{
    "servers": {
        "mcp_tenki": {
            "type": "stdio",
            "command": "${workspaceFolder}/.venv/bin/python",
            "args": [
                "${workspaceFolder}/mcp/mcp_tenki.py"
            ],
            "cwd": "${workspaceFolder}"
        }
    }
}
```

type は `stdio` or `sse` を指定します。

ローカル環境で動かすときは `stdio` です。

個人で動かすにはこれでいいのですが、他の利用者に公開したいときはどこかにサーバを立てて、そこでMCPサーバを動かしたほうがいいので、その場合は `sse` にします。

PythonのFastMCPで作るMCPサーバは、`mcp.run(transport="stdio)` もしくは `mcp.run(transport="streamable-http)` として起動しますので、これにあわせます。

commandとargsの設定は、Dockerイメージとして走らせるならこんな感じになります。

```json
"command": "docker",
"args": ["run", "-i", "--rm", "..."]
```

Pythonスクリプトを走らせるならこんな感じになります。

```json
"command": "${workspaceFolder}/.venv/bin/python",
"args": [${workspaceFolder/mcp/mcp_tenki.py}]
```

グローバル環境のPythonを使っているなら、commandは単にpython3でよいと思いますが、venvで仮想環境を作っている場合はこのような指定になります。

次に、vscodeでgithub copilotのチャットを開きます。

右下のチャットを入力する部分で「モードの設定」のドロップダウンからエージェントモードに切り替えます。

<br>

![agent](/assets/mcp_vscode_chat_mode.gif)

<br>

画面右下のスパナのマークのツールボタンをクリックしてMCPサーバを有効にします。

<br>

![vscode](/assets/mcp_vscode_workspace.gif)

<br>

これでAgentモードのチャット画面で指示を出せるようになります。

MCPサーバの利用を停止する場合、
Ctrl-Shift-Pでコマンドパレットを開いて、mcpと入力して、
サーバの一覧表示、からサーバの停止を指示できます。

MCPサーバを使う時には「実行しますか？」と聞かれるので、常に許可しておくと手間が省けます。

<br>

例：MCPサーバのファイルを指定、実行パラメータも指定する場合

```text
#file:mcp_pyats.py

ラボ名 "test lab"
ノード名 "R1"
コマンド "show ip route"
を実行して
```

<br>

```text
ラボ名 "test lab"、ノード名 "R1" で "show ip route" コマンドを実行した結果は以下の通りです。

Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area
       N1 - OSPF NSSA external type 1, N2 - OSPF NSSA external type 2
       E1 - OSPF external type 1, E2 - OSPF external type 2, m - OMP
       n - NAT, Ni - NAT inside, No - NAT outside, Nd - NAT DIA
       i - IS-IS, su - IS-IS summary, L1 - IS-IS level-1, L2 - IS-IS level-2
       ia - IS-IS inter area, * - candidate default, U - per-user static route
       H - NHRP, G - NHRP registered, g - NHRP registration summary
       o - ODR, P - periodic downloaded static route, l - LISP
       a - application route
       + - replicated route, % - next hop override, p - overrides from PfR
       & - replicated local route overrides by connected

Gateway of last resort is not set

      192.168.255.0/32 is subnetted, 2 subnets
C        192.168.255.1 is directly connected, Loopback0
i L1     192.168.255.2 [115/20] via 192.168.255.2, 01:27:06, Ethernet0/1
                       [115/20] via 192.168.255.2, 01:27:06, Ethernet0/0

必要に応じて他のコマンドも実行できますので、お知らせください。
```


<br><br>

例：自然言語で曖昧な指示する場合

```text
test labの中にあるR2のルーティングテーブルを調べて
```

<br>

```text
「test lab」のR2ノードのルーティングテーブルは以下の通りです。


Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area
       N1 - OSPF NSSA external type 1, N2 - OSPF NSSA external type 2
       E1 - OSPF external type 1, E2 - OSPF external type 2, m - OMP
       n - NAT, Ni - NAT inside, No - NAT outside, Nd - NAT DIA
       i - IS-IS, su - IS-IS summary, L1 - IS-IS level-1, L2 - IS-IS level-2
       ia - IS-IS inter area, * - candidate default, U - per-user static route
       H - NHRP, G - NHRP registered, g - NHRP registration summary
       o - ODR, P - periodic downloaded static route, l - LISP
       a - application route
       + - replicated route, % - next hop override, p - overrides from PfR
       & - replicated local route overrides by connected

Gateway of last resort is not set

      192.168.255.0/32 is subnetted, 2 subnets
i L1     192.168.255.1 [115/20] via 192.168.255.1, 01:29:06, Ethernet0/1
                       [115/20] via 192.168.255.1, 01:29:06, Ethernet0/0
C        192.168.255.2 is directly connected, Loopback0

他にも調べたいノードやコマンドがあれば教えてください。
```

<br>

例：もっと曖昧に指示する場合

```text
ラボ "test lab" のR1からR2にpingできますか？
```

<br>

```text
ラボ "test lab" のR1からR2（192.168.255.2）へのpingは成功しています。

Success rate is 100 percent (5/5), round-trip min/avg/max = 1/1/2 ms

問題なく到達可能です。
```

<br>

例：どうやって必要なパラメータを得たか質問した場合

```text
あなたはどうやってR2のアドレスを知ったのですか？
```

<br>

```text
R2のアドレス（192.168.255.2）は、R2のルーティングテーブルの出力から「C 192.168.255.2 is directly connected, Loopback0」と記載されていたため、Loopback0インターフェースのIPアドレスとして把握しました。この情報をもとにpingコマンドの宛先としました。
```

<br>

例：複数のコマンドを実行するように指示した場合

```text
R1のルーティングテーブルと、R2のルーティングテーブルを比較してください
```