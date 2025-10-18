# Copilot Agent Instructions for expt-cml

## 概要
このリポジトリはCisco Modeling Labs (CML) のラボ自動化・検証・MCP連携を目的としたPython/Dockerベースのツール群です。ラボ構築・操作・検証・MCPサーバ連携など、複数のワークフローが混在しています。

## 主要ディレクトリ・ファイル
- `bin/` : CMLラボ作成・操作用Pythonスクリプト。例: `cml_create_lab1.py`, `cml_create_srv6_docker_lab.py`
- `mcp/` : MCPサーバ関連。`cml_mcp.py`・`cml_intman_mcp.py` など VSCode Copilot Agent連携用。
- `frr/`, `tig/`, `ubuntu_docker/` : Dockerイメージ・ノード定義・起動スクリプト群。
- `requirements.txt`, `mcp/requirements.txt` : Python依存パッケージ。
- `README.*.md` : 各種ワークフロー・手順・ノウハウ集。

## アーキテクチャ・データフロー
- CMLラボはPython (`virl2_client`) でAPI操作。環境変数または `bin/cml_env` でCML接続情報を管理。
- Dockerノードは `node_definition`/`image_definition` をYAMLで指定。設定ファイルは辞書型で渡す。
- MCPサーバは `FastMCP` を利用。VSCode Copilot Agentからラボ操作コマンドを受け付ける。
- MCPサーバ起動は `stdio`/`sse` の2方式。ローカルは `stdio`、共有は `sse`。

## 開発・運用ワークフロー
- Python仮想環境は `venv` 推奨。`pip install -r requirements.txt` で依存解決。
- CMLラボ作成は `bin/` のスクリプトを直接実行。例: `python bin/cml_create_lab1.py`
- MCPサーバは `python mcp/cml_mcp.py` で起動。VSCode `.vscode/mcp.json` でサーバ設定。
- Dockerイメージは各ディレクトリの `Dockerfile`/`Makefile`/`start.sh` で管理。
- ラボノードの設定はYAMLでダウンロードし、`node_definition`/`image_definition` を確認。

## プロジェクト固有のパターン・注意点
- CML接続情報は環境変数優先。なければ `bin/cml_env` を参照。
- FRR(Docker)ノードの設定は複数ファイルを辞書型で渡す必要あり。
- MCPサーバのツール関数は `@mcp.tool()` デコレータで公開。
- VSCode Copilot Agent連携時は `.vscode/mcp.json` の `command`/`args` 設定に注意。
- 実験用ラボはYAMLでダウンロードし、必要なパラメータのみ抽出。

## 例: MCPサーバツール関数
```python
@mcp.tool()
async def run_command_on_cml_async(lab_title: str, node_label: str, command: str) -> str | None:
    # ...ラボノードでコマンド実行...
```

## よく使うコマンド例
- CMLラボ作成: `python bin/cml_create_lab1.py`
- MCPサーバ起動: `python mcp/cml_mcp.py`
- Dockerイメージビルド: `make -C frr`

## 参考ドキュメント
- `README.md` : 全体概要・各種手順へのリンク
- `README.mcp.md` : MCPサーバ・VSCode連携詳細
- `README.create_lab.md` : CMLラボ自動化・API利用方法

---

この内容で不明点・追加要望があればご指摘ください。