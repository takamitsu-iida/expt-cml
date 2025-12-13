#!/usr/bin/env python

#
# arcosを検証するためのラボを作成します。
#

# スクリプトを引数無しで実行したときのヘルプに使うデスクリプション
SCRIPT_DESCRIPTION = 'create arcos test lab'

# ラボの名前のデフォルト値
LAB_TITLE = "arcos_test_lab"

# ラボのデスクリプションのデフォルト値
LAB_DESCRIPTION = "ArcOS test lab created by cml_create_arcos_lab.py"

# 管理LANのスイッチのラベル
MA_SWITCH_LABEL = "ma-switch"

# ArcOSのノード定義名
NODE_DEFINITION = "arcos"

# ローカルファイルから踏み台サーバに関する情報を取得する

try:
    from cml_create_jumphost import UBUNTU_HOSTNAME, UBUNTU_USERNAME, UBUNTU_ENS3
except ImportError:
    UBUNTU_HOSTNAME = "jumphost"
    UBUNTU_USERNAME = "cisco"
    UBUNTU_ENS3 = "192.168.0.100/24"


###########################################################

#
# 標準ライブラリのインポート
#
import argparse
import logging
import os
import sys

from pathlib import Path

#
# 外部ライブラリのインポート
#
try:
    from dotenv import load_dotenv
    from jinja2 import Template

    # SSL Verification disabled のログが鬱陶しいので、ERRORのみに抑制
    logging.getLogger("virl2_client.virl2_client").setLevel(logging.ERROR)
    from virl2_client import ClientLibrary
    from virl2_client.models.lab import Lab, Node, NodeNotFound
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

#
# ログ設定
#

# ログファイルの名前
log_file = app_path.with_suffix('.log').name

# ログファイルを置くディレクトリ
log_dir = app_home.joinpath('log')
log_dir.mkdir(exist_ok=True)

# ログファイルのパス
log_path = log_dir.joinpath(log_file)

# ロギングの設定
# レベルはこの順で下にいくほど詳細になる
#   logging.CRITICAL
#   logging.ERROR
#   logging.WARNING --- 初期値はこのレベル
#   logging.INFO
#   logging.DEBUG
#
# ログの出力方法
# logger.debug('debugレベルのログメッセージ')
# logger.info('infoレベルのログメッセージ')
# logger.warning('warningレベルのログメッセージ')

# 独自にロガーを取得するか、もしくはルートロガーを設定する

# ルートロガーを設定する場合
# logging.basicConfig()

# 独自にロガーを取得する場合
logger = logging.getLogger(__name__)

# 参考
# ロガーに特定の名前を付けておけば、後からその名前でロガーを取得できる
# logging.getLogger("main.py").setLevel(logging.INFO)

# ログレベル設定
logger.setLevel(logging.INFO)

# フォーマット
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# 標準出力へのハンドラ
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(formatter)
stdout_handler.setLevel(logging.INFO)
logger.addHandler(stdout_handler)

# ログファイルのハンドラ
file_handler = logging.FileHandler(log_path, 'a+')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

#
# ここからスクリプト
#

def create_router_config() -> str:

    P_CONFIG_J2 = \
"""
version "8.3.1.EFT1:Nov_20_25:6_11_PM [release] 2025-11-20 18:11:22"
features feature ARCOS_RIOT
 supported false
!
features feature ARCOS_ICMP_SRC_REWRITE
 supported true
!
features feature ARCOS_SUBIF
 supported true
!
features feature ARCOS_QoS
 supported false
!
features feature ARCOS_MPLS
 supported true
!
features feature ARCOS_SFLOW
 supported true
!
system hostname P{{ rid }}
system login-banner "ArcOS (c) Arrcus, Inc."
system clock timezone-name Asia/Tokyo
system ssh-server enable true
system cli commit-message true
system netconf-server enable false
system netconf-server transport ssh enable false
system restconf-server enable false
system aaa authentication admin-user admin-password $6$45.xtCxp$NHORwpgM4fwL1b.9uKcL7J89ZoOcQ6zhauB1ZivfEcWsxmFybTtdq57tQ8oxGZePYAootxKC6L6NTIZwdxpth0
system rib IPV6
!
system rib IPV4
!
interface ma1
 type    ethernetCsmacd
 mtu     1500
 enabled true
 subinterface 0
 exit
!
network-instance default
!
network-instance management
 interface ma1
 !
!
lldp interface ma1
!
routing-policy defined-sets prefix-set __IPV4_MARTIAN_PREFIX_SET__
 prefix 0.0.0.0/8 8..32
 !
 prefix 127.0.0.0/8 8..32
 !
 prefix 192.0.0.0/24 24..32
 !
 prefix 224.0.0.0/4 exact
 !
 prefix 224.0.0.0/24 exact
 !
 prefix 240.0.0.0/4 4..32
 !
!
routing-policy defined-sets prefix-set __IPV6_MARTIAN_PREFIX_SET__
 prefix ::/128 exact
 !
 prefix ::1/128 exact
 !
 prefix ff00::/8 exact
 !
 prefix ff02::/16 exact
 !
!
""".strip()

    p_config_template = Template(P_CONFIG_J2)
    P1_CONFIG = p_config_template.render({ "rid": 1 })
    P2_CONFIG = p_config_template.render({ "rid": 2 })

    return {
        "P1_CONFIG": P1_CONFIG,
        "P2_CONFIG": P2_CONFIG
    }


def connect_ma_switch(lab: Lab, nodes: list[Node]) -> None:
    try:
        ma_switch = lab.get_node_by_label(MA_SWITCH_LABEL)
    except NodeNotFound:
        logger.error(f"MA switch node '{MA_SWITCH_LABEL}' not found")
        return []

    for node in nodes:
        ma_iface = node.get_interface_by_label('ma1')
        if ma_iface is None:
            logger.error(f"Failed to get ma1 interface of node '{node.label}'")
            continue

        # MAスイッチの最初のインタフェースを取得する
        ma_switch_iface = None
        for iface in ma_switch.interfaces():
            if not iface.is_connected():
                ma_switch_iface = iface
                break

        if ma_switch_iface is None:
            logger.error(f"No available interface on MA switch '{MA_SWITCH_LABEL}' to connect to node '{node.label}'")
            continue

        # ノードのma1インタフェースとMAスイッチのインタフェースを接続する
        lab.create_link(ma_iface, ma_switch_iface, wait=True)


def create_nodes_1(lab: Lab) -> list[Node]:

    # テキストアノテーションを作成する
    text_content = \
"""
loopback0アドレス割当
10.0.255.{{ router number }}/32
2001:db8:ffff::{{ router number }}/128
""".strip()
    create_text_annotation(lab, text_content, {'text_bold': True, 'x1': -400, 'y1': 400, 'z_index': 1})

    text_content = \
"""
SRv6ロケータ MAIN
fd00:0:0:{{ router number}}::/64
""".strip()
    create_text_annotation(lab, text_content, {'text_bold': True, 'x1': -80, 'y1': 400, 'z_index': 1})

    #
    #  PE11----P1----PE13
    #       \/    \/
    #       /\    /\
    #  PE12----P2----PE14
    #

    x_grid_width = 6*40
    y_grid_width = 4*40

    # 初期座標、これがP1ノードの位置になる
    x_pos = 0
    y_pos = y_grid_width

    # P1とP2を作る
    p_nodes = []
    for rid in [1, 2]:
        node = lab.create_node(label=f"P{rid}", node_definition="arcos", x=x_pos, y=y_pos)

        # Pルータにはスマートタグを付ける
        node.add_tag("P")

        # PATTY用シリアルコンソールのタグを付ける
        # 6001 -> P1
        # 6002 -> P2
        node.add_tag(f"serial:600{rid}")

        # arcosノードのインタフェースを追加する（この時点ではまだMACアドレスは不明）
        for i in range(9):
            node.create_interface(i, wait=True)

        # ma1インタフェースのMACアドレスを設定する
        ma_iface = node.get_interface_by_label('ma1')
        if ma_iface is None:
            logger.error("Failed to get ma1 interface of arcos node")
        else:
            # MACアドレスを設定する
            ma_iface.mac_address = f"52:54:00:00:00:{rid:02d}"

        # Y座標を下にずらす
        y_pos += y_grid_width

        p_nodes.append(node)

    # Y座標をもとに戻して、X座標を左にずらす
    x_pos = -x_grid_width
    y_pos = y_grid_width

    # 左側にあるPE11, PE12ノードを作る
    pe_nodes = []
    for rid in [11, 12]:
        node = lab.create_node(label=f"PE{rid}", node_definition="arcos", x=x_pos, y=y_pos)

        # PATTY用シリアルコンソールのタグを付ける
        # 6011 -> P11
        # 6012 -> P12
        node.add_tag(f"serial:60{rid}")

        # arcosノードのインタフェースを追加する（この時点ではまだMACアドレスは不明）
        for i in range(9):
            node.create_interface(i, wait=True)

        # ma1インタフェースのMACアドレスを設定する
        ma_iface = node.get_interface_by_label('ma1')
        if ma_iface is None:
            logger.error("Failed to get ma1 interface of arcos node")
        else:
            # MACアドレスを設定する
            ma_iface.mac_address = f"52:54:00:00:01:{rid:02d}"

        # Y座標を下にずらす
        y_pos += y_grid_width

        # PEノードをリストに追加
        pe_nodes.append(node)


    # 右側にあるPE13, PE14ノードを作る
    x_pos = x_grid_width
    y_pos = y_grid_width
    for rid in [13, 14]:
        node = lab.create_node(label=f"PE{rid}", node_definition="arcos", x=x_pos, y=y_pos)

        # PATTY用シリアルコンソールのタグを付ける
        # 6013 -> P13
        # 6014 -> P14
        node.add_tag(f"serial:60{rid}")

        # arcosノードのインタフェースを追加する（この時点ではまだMACアドレスは不明）
        for i in range(9):
            node.create_interface(i, wait=True)

        # ma1インタフェースのMACアドレスを設定する
        ma_iface = node.get_interface_by_label('ma1')
        if ma_iface is None:
            logger.error("Failed to get ma1 interface of arcos node")
        else:
            # MACアドレスを設定する
            ma_iface.mac_address = f"52:54:00:00:01:{rid:02d}"

        # Y座標を下にずらす
        y_pos += y_grid_width

        # PEノードをリストに追加
        pe_nodes.append(node)


    # ルータ間を接続する
    pe_intf_num = 1
    for p_node in p_nodes:
        p_intf_num = 1
        for pe_node in pe_nodes:
            p_node_intf = p_node.get_interface_by_label(f'swp{p_intf_num}')
            pe_node_intf = pe_node.get_interface_by_label(f'swp{pe_intf_num}')
            if p_node_intf is None or pe_node_intf is None:
                logger.error("Failed to get swp interface of arcos node")
            else:
                lab.create_link(p_node_intf, pe_node_intf, wait=True)
            p_intf_num += 1

        pe_intf_num += 1

    return p_nodes + pe_nodes


def create_text_annotation(lab: Lab, text_content: str, params: dict = None) -> None:
    base_params = {
        'border_color': '#00000000',
        'border_style': '',
        'rotation': 0,
        'text_bold': False,
        'text_content': text_content,
        'text_font': 'monospace',
        'text_italic': False,
        'text_size': 12,
        'text_unit': 'pt',
        'thickness': 1,
        'x1': 0.0,
        'y1': 0.0,
        'z_index': 0
    }
    if params:
        base_params.update(params)
    lab.create_annotation('text', **base_params)


def get_lab_by_title(client: ClientLibrary, title: str) -> Lab | None:
    labs = client.find_labs_by_title(title)
    return labs[0] if labs else None


def start_lab(lab: Lab) -> None:
    state = lab.state()  # STARTED / STOPPED / DEFINED_ON_CORE
    if state == 'STOPPED' or state == 'DEFINED_ON_CORE':
        logger.info(f"Starting lab '{lab.title}'")
        lab.start(wait=True)
        logger.info(f"Lab '{lab.title}' started")
    else:
        logger.info(f"Lab '{lab.title}' is already running")


def stop_lab(lab: Lab) -> None:
    state = lab.state()  # STARTED / STOPPED / DEFINED_ON_CORE
    if state == 'STARTED':
        logger.info(f"Stopping lab '{lab.title}'")
        lab.stop(wait=True)
        logger.info(f"Lab '{lab.title}' stopped")
    else:
        logger.info(f"Lab '{lab.title}' is not running")


def delete_lab(lab: Lab) -> None:
    title = lab.title
    logger.info(f"Deleting lab '{title}'")
    stop_lab(lab)
    lab.wipe()
    lab.remove()
    logger.info(f"Lab '{title}' deleted")


def is_exist_image_definition(client: ClientLibrary, image_def_id: str) -> bool:
    image_defs = client.definitions.image_definitions()
    image_def_ids = [img['id'] for img in image_defs]
    return image_def_id in image_def_ids


def create_lab(client: ClientLibrary, title: str, description: str) -> None:

    # ラボを取得する
    lab = get_lab_by_title(client, title)

    # 無ければ作成する
    if lab is None:
        lab = client.create_lab(title=title, description=description)

    # 構成パターン1
    nodes = create_nodes_1(lab)
    if not nodes:
        logger.error("Failed to create nodes")
        return

    # MAスイッチに接続する
    connect_ma_switch(lab, nodes)

    logger.info(f"Lab '{title}' created successfully")
    logger.info(f"id: {lab.id}")



def scp_to_jumphost(config_content: str, remote_path: str, mode: str = '644') -> None:
    """SCPコマンドを使ってルータの設定をデプロイする"""

    #
    # TODO: paramikoを使ってSCPで送り込むようにした方がよい？
    #

    import subprocess  # コンフィグファイルをSCPで送り込むため
    import tempfile    # 一時ファイルを作成するため

    UBUNTU_ADDRESS = UBUNTU_ENS3.split('/')[0]

    try:
        # 一時ファイルに書き込み
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.conf') as tmp:
            tmp.write(config_content)
            tmp_path = tmp.name

        # scpでファイル転送
        logger.info(f"Copying config to {UBUNTU_USERNAME}@{UBUNTU_ADDRESS}:{remote_path}")

        subprocess.run([
            'scp',
            '-o', 'StrictHostKeyChecking=no',  # 初回接続時のホスト確認をスキップ
            tmp_path,
            f'{UBUNTU_USERNAME}@{UBUNTU_ADDRESS}:{remote_path}'
        ], check=True, capture_output=True, text=True)

        # パーミッション設定
        logger.info(f"Setting permissions {mode} on {remote_path}")

        subprocess.run([
            'ssh',
            '-o', 'StrictHostKeyChecking=no',
            f'{UBUNTU_USERNAME}@{UBUNTU_ADDRESS}',
            f'chmod {mode} {remote_path}'
        ], check=True, capture_output=True, text=True)

        logger.info(f"Config deployed successfully to {remote_path}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to deploy config: {e.stderr}")
        raise
    finally:
        # 一時ファイル削除
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def upload_configs_to_jumphost(lab: Lab) -> None:

    # jumphostが起動していることを確認する

    jumphost = lab.get_node_by_label(UBUNTU_HOSTNAME)
    if jumphost is None:
        logger.error("Jumphost node not found in the lab")
        return

    if jumphost.state not in  ['STARTED', 'BOOTED']:  # STARTED / STOPPED / DEFINED_ON_CORE
        logger.error(f"Jumphost is not running. Please start the jumphost before uploading configs. Current state: {jumphost.state}")
        return

    configs = create_router_config()
    scp_to_jumphost(configs["P1_CONFIG"], "/srv/tftp/P1.conf")
    scp_to_jumphost(configs["P2_CONFIG"], "/srv/tftp/P2.conf")





if __name__ == '__main__':

    def main() -> None:

        # 引数処理
        parser = argparse.ArgumentParser(description=SCRIPT_DESCRIPTION)
        parser.add_argument('--create', action='store_true', default=False, help='Create lab')
        parser.add_argument('--delete', action='store_true', default=False, help='Delete lab')
        parser.add_argument('--stop', action='store_true', default=False, help='Stop lab')
        parser.add_argument('--start', action='store_true', default=False, help='Start lab')
        parser.add_argument('--title', type=str, default=LAB_TITLE, help=f'Lab title (default: {LAB_TITLE})')
        parser.add_argument('--description', type=str, default=LAB_DESCRIPTION, help=f'Lab description (default: {LAB_DESCRIPTION})')
        parser.add_argument('--upload', action='store_true', default=False, help='Upload configuration files to jumphost')
        args = parser.parse_args()

        # 引数が何も指定されていない場合はhelpを表示して終了
        if not any(vars(args).values()):
            parser.print_help()
            return

        # CMLを操作するvirl2_clientをインスタンス化
        try:
            client = ClientLibrary(f"https://{CML_ADDRESS}/", CML_USERNAME, CML_PASSWORD, ssl_verify=False)
        except Exception as e:
            logger.critical(f"Failed to connect to CML at {CML_ADDRESS}")
            logger.critical(str(e))
            return

        # 接続を待機する
        client.is_system_ready(wait=True)

        # 指定されたタイトルのラボを取得する
        lab = get_lab_by_title(client, args.title)

        if args.start:
            start_lab(lab) if lab else logger.error(f"Lab '{args.title}' not found")
            return

        if args.stop:
            stop_lab(lab) if lab else logger.error(f"Lab '{args.title}' not found")
            return

        if args.delete:
            delete_lab(lab) if lab else logger.error(f"Lab '{args.title}' not found")
            return

        if args.create:
            create_lab(client, args.title, args.description)
            return

        if args.upload:
            upload_configs_to_jumphost(lab) if lab else logger.error(f"Lab '{args.title}' not found")
            return

    #
    # 実行
    ##
    main()
