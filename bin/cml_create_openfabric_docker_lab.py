#!/usr/bin/env python

###########################################################

#
# 作成するラボの情報
#

# ラボの名前、既存で同じタイトルのラボがあれば削除してから作成する
LAB_NAME = "Docker FRR OpenFabric"

# このラボで使うシリアルポートの開始番号
SERIAL_PORT = 7000

# ノード定義（Docker FRR）
NODE_DEFINITION = "frr-10-4"

# イメージ定義
IMAGE_DEFINITION = "frr-10-4"

# node_cfgのテンプレート
NODE_CFG_FILENAME = "openfabric_docker_lab_node_cfg.j2"

# protocolsのテンプレート
PROTOCOLS_FILENAME = "openfabric_docker_lab_protocols.j2"

###########################################################

#
# 標準ライブラリのインポート
#
import argparse
import logging
import sys
from pathlib import Path

#
# 外部ライブラリのインポート
#
try:
    from jinja2 import Template
    from virl2_client import ClientLibrary
except ImportError as e:
    logging.critical(str(e))
    sys.exit(-1)

#
# ローカルファイルからの読み込み
#
from cml_config import CML_ADDRESS, CML_USERNAME, CML_PASSWORD

# このファイルへのPathオブジェクト
app_path = Path(__file__)

# このファイルの名前から拡張子を除いてプログラム名を得る
app_name = app_path.stem

# アプリケーションのホームディレクトリはこのファイルからみて一つ上
app_home = app_path.parent.joinpath('..').resolve()

# データ用ディレクトリ
data_dir = app_home.joinpath('data')

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
if __name__ == '__main__':

    def read_template_config(filename='') -> str:
        p = data_dir.joinpath(filename)
        try:
            with p.open() as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"{filename} not found")
            sys.exit(1)


    def main():

        # 引数処理
        parser = argparse.ArgumentParser(description='create openfabric lab')
        parser.add_argument('-d', '--delete', action='store_true', default=False, help='Delete lab')
        args = parser.parse_args()

        # CMLを操作するvirl2_clientをインスタンス化
        client = ClientLibrary(f"https://{CML_ADDRESS}/", CML_USERNAME, CML_PASSWORD, ssl_verify=False)

        # 接続を待機する
        client.is_system_ready(wait=True)

        # 同タイトルのラボを消す
        for lab in client.find_labs_by_title(LAB_NAME):
            lab.stop(wait=True)
            lab.wipe()
            lab.remove()

        # -d で起動していたらここで処理終了
        if args.delete:
            return 0

        # ラボを新規作成
        lab = client.create_lab(title=LAB_NAME)

        # (X, Y)座標
        x = 0
        y = 0
        grid_width = 160

        # 外部接続用のブリッジを作る
        ext_conn_node = lab.create_node("bridge1", "external_connector", x, y)

        # デフォルトはNATなので、これを"bridge1"に変更する
        # bridge1は追加したブリッジで、インターネット接続はない
        # このLANに足を出せば、別のラボの仮想マシンであっても通信できる
        ext_conn_node.configuration = "bridge1"

        # bridge1に接続するスイッチ（アンマネージド）を作る
        # 場所はブリッジの下
        y += grid_width
        ext_switch_node = lab.create_node("ext-sw", "unmanaged_switch", x, y)

        # bridge1とスイッチを接続する
        lab.connect_two_nodes(ext_conn_node, ext_switch_node)

        # FRRに設定するnode.cfgのJinja2テンプレートを取り出す
        node_cfg_j2 = read_template_config(filename=NODE_CFG_FILENAME)

        # Jinja2のTemplateをインスタンス化する
        node_cfg_template = Template(node_cfg_j2)

        # node_cfg_templateに渡すコンテキストオブジェクトの初期値
        node_cfg_context = {
            "HOSTNAME": "R",
            "IPv4_ROUTER_ID": "",
            "IPv6_ROUTER_ID": "",
            "TIER": "0",
        }

        # FRRに設定するprotocolsのJinja2テンプレートを取り出す
        protocols_j2 = read_template_config(filename=PROTOCOLS_FILENAME)

        # Jinja2のTemplateをインスタンス化する
        protocols_template = Template(protocols_j2)

        # templateに渡すコンテキストオブジェクト
        protocols_context = {}

        # FRRに設定するprotocolsのテキストを作る
        protocols_text = protocols_template.render(protocols_context)

        # ルータを区別するための番号
        router_number = 1

        # openfabricの用語では末端に近いところからT0、T1の順で呼ぶ
        # ここでは３階層のネットワークを作るのでT0, T1, T2を作る。

        # 作成するt2ノードを格納しておくリスト
        t2_nodes = []

        # T2のFRRを3個作る
        x += grid_width
        for i in range(3):
            # Y座標
            y = i * grid_width

            # ノードをインスタンス化する関数はこれ
            # create_node(
            #   label: str,
            #   node_definition: str,
            #   x: int = 0, y: int = 0,
            #   wait: bool | None = None,
            #   populate_interfaces: bool = False, **kwargs
            # )→ Node

            # ルータの名前
            node_name = f"R{router_number}"

            # その名前でFRRをインスタンス化する
            node = lab.create_node(node_name, NODE_DEFINITION, x, y)

            # インタフェースを作成する
            for _ in range(8):
                node.create_interface(_, wait=True)

            # 起動イメージを指定する
            node.image_definition = IMAGE_DEFINITION

            # スマートタグを設定
            node.add_tag(tag="TIER2")

            # ノード個別のタグを設定
            # 例 serial:7001
            node_tag = f"serial:{SERIAL_PORT + router_number}"
            node.add_tag(tag=node_tag)

            # 外部接続用スイッチと接続
            # lab.connect_two_nodes(ext_switch_node, node)

            # FRRの設定を作る
            node_cfg_context["HOSTNAME"] = node_name
            node_cfg_context["IPv4_ROUTER_ID"] = str(router_number)
            node_cfg_context["IPv6_ROUTER_ID"] = "{:0=2}".format(router_number)
            node_cfg_context["TIER"] = "2"
            node_cfg_text = node_cfg_template.render(node_cfg_context)

            # FRRに設定するファイル一式
            frr_configurations = [
                {
                    'name': 'node.cfg',
                    'content': node_cfg_text
                },
                {
                    'name': 'protocols',
                    'content': protocols_text
                }
            ]

            # FRRノードに設定を適用する
            node.configuration = frr_configurations

            # リストに追加する
            t2_nodes.append(node)

            # ルータを作ったので一つ数字を増やす
            router_number += 1

        # 続いてT1クラスタを2個作る
        x += grid_width
        y = 0
        num_clusters = 2
        for i in range(num_clusters):

            # クラスタ内のスパインルータ（T1ルータ）を格納するリスト
            t1_nodes = []

            # クラスタ内にT1ルータを2個作る
            for j in range(2):
                node_name = f"R{router_number}"
                node = lab.create_node(node_name, NODE_DEFINITION, x, y)
                y += grid_width

                # インタフェースを作成する
                for _ in range(8):
                    node.create_interface(_, wait=True)

                # 起動イメージを指定
                node.image_definition = IMAGE_DEFINITION

                # スマートタグを設定
                node.add_tag(tag=f"cluster-{i + 1}")

                # ノード個別のタグを設定
                # 例 serial:7201
                node_tag = f"serial:{SERIAL_PORT + router_number}"
                node.add_tag(tag=node_tag)

                # FRRの設定を作る
                node_cfg_context["HOSTNAME"] = node_name
                node_cfg_context["IPv4_ROUTER_ID"] = str(router_number)
                node_cfg_context["IPv6_ROUTER_ID"] = "{:0=2}".format(router_number)
                node_cfg_context["TIER"] = "1"
                node_cfg_text = node_cfg_template.render(node_cfg_context)

                # FRRに設定するファイル一式
                frr_configurations = [
                    {
                        'name': 'node.cfg',
                        'content': node_cfg_text
                    },
                    {
                        'name': 'protocols',
                        'content': protocols_text
                    }
                ]

                # FRRノードに設定を適用する
                node.configuration = frr_configurations

                # tier1ルータと接続する
                for n in t2_nodes:
                    lab.connect_two_nodes(n, node)

                # リストに追加
                t1_nodes.append(node)

                router_number += 1


            # 続いてクラスタ内にT0ルータを作る
            t0_x = x + grid_width
            t0_y = i * grid_width * 2 + int(grid_width / 2)
            for k in range(3):

                node_name = f"R{router_number}"
                node = lab.create_node(node_name, NODE_DEFINITION, t0_x, t0_y)
                t0_x += grid_width

                # インタフェースを作成する
                for _ in range(8):
                    node.create_interface(_, wait=True)

                # 起動イメージを指定
                node.image_definition = IMAGE_DEFINITION

                # スマートタグを設定
                node.add_tag(tag=f"cluster-{i + 1}")

                # ノード個別のタグを設定
                # 例 serial:7301
                node_tag = f"serial:{SERIAL_PORT + router_number}"
                node.add_tag(tag=node_tag)

                # FRRの設定を作る
                node_cfg_context["HOSTNAME"] = node_name
                node_cfg_context["IPv4_ROUTER_ID"] = str(router_number)
                node_cfg_context["IPv6_ROUTER_ID"] = "{:0=2}".format(router_number)
                node_cfg_context["TIER"] = "0"
                node_cfg_text = node_cfg_template.render(node_cfg_context)

                # FRRに設定するファイル一式
                frr_configurations = [
                    {
                        'name': 'node.cfg',
                        'content': node_cfg_text
                    },
                    {
                        'name': 'protocols',
                        'content': protocols_text
                    }
                ]

                # FRRノードに設定を適用する
                node.configuration = frr_configurations

                # Tier2と接続
                for n in t1_nodes:
                    lab.connect_two_nodes(n, node)

                router_number += 1


        # start the lab
        # lab.start()

        # print nodes and interfaces states:
        #for node in lab.nodes():
        #    print(node, node.state, node.cpu_usage)
        #    for interface in node.interfaces():
        #        print(interface, interface.readpackets, interface.writepackets)

        return 0

    # 実行
    sys.exit(main())
