#!/usr/bin/env python

# スクリプトを引数無しで実行したときのヘルプに使うデスクリプション
SCRIPT_DESCRIPTION = "List all labs in Cisco Modeling Labs (CML)"

#
# 標準ライブラリのインポート
#
import logging
import os
import sys

from pathlib import Path

#
# 外部ライブラリのインポート
#
try:
    from dotenv import load_dotenv

    # SSL Verification disabled のログが鬱陶しいので、ERRORのみに抑制
    logging.getLogger("virl2_client.virl2_client").setLevel(logging.ERROR)
    from virl2_client import ClientLibrary
    from virl2_client.models.lab import Lab

    import tabulate
except ImportError as e:
    logging.critical(str(e))
    sys.exit(-1)

# このファイルへのPathオブジェクト
app_path = Path(__file__)

# このファイルがあるディレクトリ
app_dir = app_path.parent

# このファイルの名前から拡張子を除いてプログラム名を得る
app_name = app_path.stem

# アプリケーションのホームディレクトリはこのファイルからみて一つ上
app_home = app_path.parent.joinpath('..').resolve()

#
# CMLに接続するための情報を取得する
#

# まず環境変数を取得
CML_ADDRESS = os.getenv("VIRL2_URL") or os.getenv("VIRL_HOST")
CML_USERNAME = os.getenv("VIRL2_USER") or os.getenv("VIRL_USERNAME")
CML_PASSWORD = os.getenv("VIRL2_PASS") or os.getenv("VIRL_PASSWORD")

# 環境変数が未設定ならcml_envファイルから読み取る
if not all([CML_ADDRESS, CML_USERNAME, CML_PASSWORD]):
    env_path = app_dir.joinpath('cml_env')
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path)
        CML_ADDRESS = os.getenv("VIRL2_URL") or os.getenv("VIRL_HOST")
        CML_USERNAME = os.getenv("VIRL2_USER") or os.getenv("VIRL_USERNAME")
        CML_PASSWORD = os.getenv("VIRL2_PASS") or os.getenv("VIRL_PASSWORD")

# 接続情報を得られなかったら終了
if not all([CML_ADDRESS, CML_USERNAME, CML_PASSWORD]):
    logging.critical("CML connection info not found in environment variables or cml_env file")
    sys.exit(-1)


def get_lab_titles() -> list[str]:
    try:
        client = ClientLibrary(CML_ADDRESS, CML_USERNAME, CML_PASSWORD, ssl_verify=False)
    except Exception as e:
        logging.error(f"CMLへの接続に失敗しました: {e}")
        return []
    labs = client.all_labs()
    return [lab.title for lab in labs] if labs else []


def get_lab_by_title(lab_title: str) -> Lab | None:
    try:
        client = ClientLibrary(CML_ADDRESS, CML_USERNAME, CML_PASSWORD, ssl_verify=False)
    except Exception as e:
        logging.error(f"CMLへの接続に失敗しました: {e}")
        return None
    labs = client.find_labs_by_title(lab_title)
    lab = labs[0] if labs else None
    if not lab:
        logging.error(f"ラボ '{lab_title}' が見つかりません")
        return None
    return lab


def get_lab_status_by_title(lab_title: str) -> str:
    lab = get_lab_by_title(lab_title)
    if not lab:
        return "NOT FOUND"
    return lab.state()


def get_node_labels(lab_title: str) -> list[str]:
    lab = get_lab_by_title(lab_title)
    if not lab:
        return None

    nodes = lab.nodes()
    return [node.label for node in nodes] if nodes else []


def get_node_by_label(lab: Lab, node_label: str):
    if lab.state() != 'STARTED':
        logging.error(f"ラボ '{lab.title()}' は起動していません")
        return None

    try:
        node = lab.get_node_by_label(node_label)
    except Exception as e:
        logging.error(f"ノード '{node_label}' が見つかりません: {e}")
        return None

    return node


def run_command_on_device(lab_title: str, node_label: str, command: str) -> str | None:
    """Run a command on the device in exec mode.
    """
    lab = get_lab_by_title(lab_title)
    if not lab:
        return None

    node = get_node_by_label(lab, node_label)
    if not node:
        return None

    try:
        lab.pyats.sync_testbed(CML_USERNAME, CML_PASSWORD)
    except Exception as e:
        logging.error(f"pyATS testbedの同期に失敗しました: {e}")
        return None

    try:
        result = node.run_pyats_command(command)
    except Exception as e:
        logging.error(f"コマンドの実行に失敗しました: {e}")
        return None

    return result


def run_config_command_on_device(lab_title: str, node_label: str, command: str) -> str | None:
    """Run a command on the device in configure mode.
    """
    lab = get_lab_by_title(lab_title)
    if not lab:
        return None

    node = lab.get_node_by_label(node_label)
    if not node:
        return None

    try:
        lab.pyats.sync_testbed(CML_USERNAME, CML_PASSWORD)
    except Exception as e:
        logging.error(f"pyATS testbedの同期に失敗しました: {e}")
        return None

    try:
        result = node.run_pyats_config_command(command)
    except Exception as e:
        logging.error(f"コンフィグコマンドの実行に失敗しました: {e}")
        return None

    return result


if __name__ == "__main__":

    lab_titles = get_lab_titles()
    if not lab_titles:
        print("No labs found.")
        sys.exit(0)

    table = []
    for title in lab_titles:
        status = get_lab_status_by_title(title)
        table.append([title, status])

    print(tabulate.tabulate(table, headers=["Lab Title", "Status"]))