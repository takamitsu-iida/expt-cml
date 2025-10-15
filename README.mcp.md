# Visual Studio CodeからMCPでCMLのラボを操作する

PythonでMCPサーバを作成して、Visual Studio CodeのCopilotで利用できるようにします。


<br><br>

## MCPサーバ

ラボの操作にvirl2_clientモジュールを使いたいので、PythonでMCPサーバを作ります。

[FastMCP](https://gofastmcp.com/getting-started/welcome)を使うと簡単にMCPサーバを実装できます。

FastMCPはpipでインストールできます。

<br>

```bash
pip install -r mcp/requirements.txt
```

<br>

FastMCPの使い方は簡単です。

ラボ内のノードにコマンドを送り込む関数を作ったら、こんな感じでデコレータを被せるだけでMCPサーバのツールになります。

```python
if __name__ == "__main__":
    #
    # MCPサーバ初期化
    #
    mcp = FastMCP(SCRIPT_DESCRIPTION)

    # グローバルなスレッドプールを1つだけ用意
    thread_pool_executor = concurrent.futures.ThreadPoolExecutor()

    @mcp.tool()
    async def run_command_on_cml_async(lab_title: str, node_label: str, command: str) -> str | None:
        """
        指定したCMLラボのノードでコマンドを実行します。

        Args:
            lab_title: ラボのタイトル
            node_label: ノードのラベル
            command: 実行するコマンド

        Returns:
            コマンドの実行結果（str）またはNone
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            thread_pool_executor,
            run_command_on_cml,
            lab_title,
            node_label,
            command
        )
```

<br>

[mcp_pyats.py](/mcp/mcp_pyats.py) はわずか300行にも満たない短いスクリプトですが、
これをGithub Copilotのエージェントモードから利用すると、驚くような効果を発揮します。

<br><br>

## Visual Studio CodeのMCP設定

独自のMCPサーバを使うには、vscodeに設定が必要です。

<br>

> [!NOTE]
>
> Copilotの契約によってはvscodeでのMCP利用に制限がかかっていることがあります。
>
> 設定画面が以下のようになっている場合、MCPサーバを利用できませんので、別のツールを使ってください。
>
> ![vscode](/assets/mcp_vscode_organization.png)

<br>

ここでは特定のワークスペースの中だけで利用できるように設定します。

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
        "mcp_pyats": {
            "type": "stdio",
            "command": "${workspaceFolder}/.venv/bin/python",
            "args": [
                "${workspaceFolder}/mcp/cml_mcp.py"
            ],
            "cwd": "${workspaceFolder}"
        }
    },
    "inputs": []
}
```

type は `stdio` or `sse` を指定します。

ローカル環境で動かすときは `stdio` です。

個人で動かすにはこれでいいのですが、他のユーザにも利用して欲しいときはどこかにサーバを立てて、そこでMCPサーバを動かしたほうがいいので、その場合は `sse` にします。

PythonのFastMCPで作るMCPサーバは、`mcp.run(transport="stdio)` もしくは `mcp.run(transport="streamable-http)` として起動しますので、これにあわせます。

commandとargsで実行方法を指定します。

Dockerイメージとして走らせるならこんな感じになります。

```json
"command": "docker",
"args": ["run", "-i", "--rm", "..."]
```

Pythonスクリプトを走らせるならこんな感じになります。

```json
"command": "${workspaceFolder}/.venv/bin/python",
"args": [ "${workspaceFolder}/mcp/mcp_tenki.py" ]
```

グローバル環境のPythonを使っているなら、commandは単にpython3でよいと思いますが、venvで仮想環境を作っている場合は上記のような指定になります。

<br>

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

<br><br><br>

## 動作例

このラボ（ラボタイトルはtest lab）を使って実験してみます。

<br>

![lab](/assets/intman-lab.png)

<br>

### コマンドを実行して

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

<br>

### ルーティングテーブルを調べて

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

### pingできる？

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

### どうやって調べた？

```text
あなたはどうやってR2のアドレスを知ったのですか？
```

<br>

```text
R2のアドレス（192.168.255.2）は、
R2のルーティングテーブルの出力から「C 192.168.255.2 is directly connected, Loopback0」と記載されていたため、
Loopback0インターフェースのIPアドレスとして把握しました。

この情報をもとにpingコマンドの宛先としました。
```

<br>

### 隣接ノードを取得して

```text
cdpを使ってR1の隣接ノードを取得してください
```

<br>

```text
R1のCDP隣接ノード情報は以下の通りです。

隣接ノード: R2
  接続インターフェース: Ethernet0/0, Ethernet0/1

R1はR2と2つのインターフェース（Eth0/0, Eth0/1）で隣接しています。
```

<br>

### CDPを停止して

```text
R1の設定を変更してください。CDPを停止してください。
```

<br>

```text
R1の設定を変更し、CDPを停止しました（no cdp run を投入しました）。

これでR1上でCDPは無効化されています。
```

<br>

### もう一度、隣接ルータの情報を取得して

```text
R1の隣接ルータの情報を表示してください。
```

<br>

```text
R1でCDPは無効化されているため、隣接ルータ情報は表示できません（% CDP is not enabled）。
CDPを再度有効化することで隣接情報の取得が可能になります。必要であればお知らせください。
```

<br>

### ISISの隣接状態を取得して

```text
R1の隣接ルータの情報をISISの情報から取得してください
```

<br>

```text
R1のIS-IS隣接ルータ情報は以下の通りです。


System Id   Type  Interface  IP Address      State  Holdtime  Circuit Id
R2          L1L2  Et0/0      192.168.255.2   UP     24        01
R2          L1L2  Et0/1      192.168.255.2   UP     29        02

R1はR2とEthernet0/0およびEthernet0/1でIS-IS隣接関係を確立しています。
```
