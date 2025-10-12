# MCPメモ

<br>

## Visual Studio Codeで使う


`.vscode` ディレクトリを作成

```bash
mkdir .vscode
```

新しいファイル `mcp.json` を作成する

エディタの右下に「サーバの追加」とうボタンが登場するので、それをクリック

<br>

![vscode](/assets/mcp_vscode_workspace.gif)

<br>


```json
{
	"servers": {
		"my-mcp-server": {
			"type": "stdio",
			"command": "/usr/bin/env python",
			"args": ["${workspaceFolder}/mcp/mcp_server.py"]
		}
	},
	"inputs": []
}
```

- type は接続のタイプ `stdio` or `sse`

ローカル環境で動かすときは `stdio` でよい。リモートサーバを使うなら `sse` にする。

Dockerイメージを走らせるならこんな感じ

```json
"command": "docker",
"args": ["run", "-i", "--rm", "..."]
```

vscodeでgithub copilotのチャットを開く

右下のチャットを入力する部分で、「モードの設定」のドロップダウンからエージェントに切り替える

<br>

![agent](/assets/mcp_vscode_chat_mode.gif)

<br>


この時点ではまだ自作のMCPサーバは有効になっていない

画面右下のスパナのマークのツールボタンをクリックして、MCPサーバを有効にする。

<br>

![vscode](/assets/mcp_vscode_workspace.gif)

<br>

これでチャット画面で「my_mcp_serverを実行してください」といった具合で指示を出せるようになる。

起動時に　実行しますか？　と聞かれるので、常に許可しておくと手間が省ける。

Ctrl-Shift-Pでコマンドパレットを開いて、mcpと入力して、サーバの一覧表示、からサーバの開始停止を指示できる。