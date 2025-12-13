import getpass
import json

CONFIG_FILE = "cml_env"

def create_config():
    """ユーザー入力を受け付け、設定ファイルを生成する"""
    print("--- サーバー接続情報の設定 ---")

    # 対話的に情報を取得
    server_ip = input("サーバーのIPアドレスを入力してください: ")
    username = input("ユーザー名を入力してください: ")

    # パスワードは入力内容を隠すgetpassを使用
    # パスワードは標準入力から秘密裏に入力させる
    try:
        password = getpass.getpass("パスワードを入力してください: ")
    except EOFError:
        print("\n入力が途中で中断されました。")
        return

    # 設定辞書を作成
    config_data = {
        "ip_address": server_ip,
        "user": username,
        "password": password  # 注意: プレーンテキストで保存される
    }

    # 設定ファイルとしてJSON形式で保存
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=4)
        print(f"\n✅ 設定ファイル '{CONFIG_FILE}' を正常に作成しました。")
    except IOError as e:
        print(f"\n❌ 設定ファイルの書き込みに失敗しました: {e}")

if __name__ == "__main__":
    create_config()