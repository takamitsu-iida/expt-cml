#!/bin/bash
# ----------------------------------------------------------------------
# setup.sh: 依存ツール (python, pip, direnv) のインストール、
#             Python依存性のインストール、設定ファイル生成を一括で実行します。
# ----------------------------------------------------------------------

# 実行前に管理者権限が必要であることを通知
echo "このスクリプトは、必要な開発ツールをシステムにインストールするため、"
echo "管理者権限 (sudo) を必要とすることがあります。"
echo "----------------------------------------------------"

# 必要なパッケージをインストールする関数
install_tools() {
    local packages_to_install=()
    local install_cmd=""

    # 必要なツール（python3, pip3, direnv）の有無をチェック
    if ! command -v python3 >/dev/null; then
        packages_to_install+=(python3)
    fi
    if ! command -v direnv >/dev/null; then
        packages_to_install+=(direnv)
    fi

    if [ ${#packages_to_install[@]} -eq 0 ] && command -v pip3 >/dev/null; then
        echo "python3, pip3, direnvは既にインストールされています。スキップします。"
        return 0
    fi

    echo "不足している開発ツール (${packages_to_install[*]}) のインストールを開始します..."

    # Debian/Ubuntu (apt)
    if command -v apt >/dev/null; then
        echo "--> Debian/Ubuntu環境を検出"
        sudo apt update
        # python3-pip, direnvをインストール (python3-venvは通常python3に含まれる)
        install_cmd="sudo apt install -y python3 python3-pip python3-venv direnv"

    # RHEL/Fedora/CentOS (dnf/yum)
    elif command -v dnf >/dev/null; then
        echo "--> RHEL/Fedora/CentOS環境 (dnf) を検出"
        install_cmd="sudo dnf install -y python3 python3-pip python3-venv direnv"

    elif command -v yum >/dev/null; then
        echo "--> CentOS環境 (yum) を検出"
        install_cmd="sudo yum install -y python3 python3-pip python3-venv direnv"

    # openSUSE/SUSE (zypper)
    elif command -v zypper >/dev/null; then
        echo "--> openSUSE/SUSE環境を検出"
        install_cmd="sudo zypper install -y python3 python3-pip python3-venv direnv"

    else
        echo "⚠️ 互換性のあるパッケージマネージャーが見つかりませんでした。"
        echo "python3, python3-pip, direnvを手動でインストールしてください。"
        exit 1
    fi

    # インストールコマンドを実行
    if [ -n "$install_cmd" ]; then
        eval "$install_cmd"
        if [ $? -ne 0 ]; then
            echo "❌ 開発ツールのインストール中にエラーが発生しました。"
            exit 1
        fi
    fi
}

# direnvをシェルにフックする関数 (前回のものと変更なし)
setup_direnv_hook() {
    local hook_line='eval "$(direnv hook bash)"'
    local rc_file=""

    if [ -n "$BASH_VERSION" ] && [ -f "$HOME/.bashrc" ]; then
        rc_file="$HOME/.bashrc"
    elif [ -n "$ZSH_VERSION" ] && [ -f "$HOME/.zshrc" ]; then
        rc_file="$HOME/.zshrc"
    else
        echo "⚠️ direnvのフックを自動で設定できませんでした。"
        echo "手動でシェル設定ファイル (.bashrcまたは.zshrc) に以下を追記してください:"
        echo "    $ hook_line"
        return
    fi

    if ! grep -q "$hook_line" "$rc_file"; then
        echo "" >> "$rc_file"
        echo "# direnv hook added by install.sh" >> "$rc_file"
        echo "$hook_line" >> "$rc_file"
        echo "✅ direnvフックを $rc_file に追記しました。"
        echo "変更を有効にするため、このターミナルセッションを再起動するか、"
        echo " 'source $rc_file' を実行してください。"
    else
        echo "✅ direnvフックは $rc_file に既に設定されています。"
    fi
}

# direnvの設定ファイル（.envrc）を処理する関数 (前回のものと変更なし)
setup_envrc() {
    if [ -f .envrc ]; then
        echo "⚠️ .envrc が既に存在します。上書きを避けるため、自動設定はスキップします。"
        echo "プロジェクトのPython仮想環境を使用するには、手動で以下の行を .envrc に追記してください:"
        echo "    export VIRTUAL_ENV_DISABLE_PROMPT=1"
        echo "    layout python"
    else
        echo "export VIRTUAL_ENV_DISABLE_PROMPT=1" > .envrc
        echo 'layout python' >> .envrc
        echo "✅ .envrc ファイルを作成しました。direnvが環境を自動で設定します。"
    fi

    if command -v direnv >/dev/null; then
        echo "--- direnvにこのディレクトリを信頼させます ---"
        direnv allow .
    fi
}

# Pythonの依存関係をインストールする関数
install_python_deps() {
    if [ ! -f "../requirements.txt" ]; then
        echo "⚠️ requirements.txt が見つかりません。Python依存性のインストールをスキップします。"
        return 0
    fi

    # 仮想環境が有効であることを確認 (direnvが動作しない環境へのフォールバックを兼ねる)
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "--- 仮想環境 (.venv) を作成します ---"
        python3 -m venv .venv
        source .venv/bin/activate
    fi

    echo "--- requirements.txtからPythonモジュールをインストール中 ---"
    python3 -m pip install -r ../requirements.txt

    if [ $? -ne 0 ]; then
        echo "❌ Python依存性のインストール中にエラーが発生しました。"
        return 1
    fi

    # スクリプト内で activate した場合、ディアクティベートは不要
    return 0
}

# 設定ファイル生成スクリプトを実行する関数
run_config_script() {
    if [ ! -f "setup_config.py" ]; then
        echo "❌ setup_config.py が見つかりません。設定ファイルの作成をスキップします。"
        return 1
    fi

    echo "--- サーバー接続情報の設定を開始します ---"
    python3 setup_config.py

    if [ $? -ne 0 ]; then
        echo "❌ 設定ファイルの作成中にエラーが発生しました。"
        return 1
    fi
    return 0
}

# =================================================================
# メイン処理の実行
# =================================================================

# 1. 開発ツールをインストール
install_tools

# 2. direnvのフック設定
setup_direnv_hook

# 3. direnvの設定ファイル（.envrc）の処理
setup_envrc

# 4. Pythonの依存関係をインストール
install_python_deps
if [ $? -ne 0 ]; then exit 1; fi

# 5. 設定ファイル生成スクリプトの実行
run_config_script
if [ $? -ne 0 ]; then exit 1; fi


echo "✅ 全てのセットアップが正常に完了しました！"
echo "---"
echo "次のステップ: 新しいターミナルを開くか、'source ~/.bashrc' を実行してから、プロジェクト作業を開始してください。"
exit 0