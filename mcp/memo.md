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

これでチャット画面で「my_mcp_serverを実行してください」といった具合で指示を出せるようになります。

MCPサーバ起動時には「実行しますか？」と聞かれるので、常に許可しておくと手間が省けます。

Ctrl-Shift-Pでコマンドパレットを開いて、mcpと入力して、サーバの一覧表示、からサーバの開始停止を指示できます。
