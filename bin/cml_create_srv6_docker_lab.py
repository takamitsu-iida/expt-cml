#!/usr/bin/env python

###########################################################

#
# 作成するラボの情報
#

# ラボの名前、既存で同じタイトルのラボがあれば削除してから作成する
LAB_NAME = "Docker FRR SRv6"

# このラボで使うシリアルポートの開始番号
SERIAL_PORT = 5000

# ノード定義（Docker FRR）
NODE_DEFINITION = "frr-10-4"

# イメージ定義
IMAGE_DEFINITION = "frr-10-4"

# protocolsファイルの内容
PROTOCOLS_TEXT = """\
bgpd
# ospfd
# ospf6d
# ripd
# ripngd
isisd
# pimd
# pim6d
# ldpd
# nhrpd
# eigrpd
# babeld
# sharpd
# pbrd
# bfdd
# fabricd
# vrrpd
# pathd
"""

CONFIG_TEMPLATE = """\
!
integrated-vtysh-config
!
hostname {{ HOSTNAME }}
ip router-id 192.168.255.{{ ROUTER_NUMBER }}
!
{{ INTERFACES }}
!
interface lo
 ip address 192.168.255.{{ ROUTER_NUMBER }}/32
 ip router isis 1
 ipv6 address 2001:db8:ffff::{{ ROUTER_NUMBER }}/128
 ipv6 address fd00:1:{{ ROUTER_NUMBER }}::/128
 ipv6 router isis 1
exit
!
router isis 1
 is-type level-1
 net 49.0001.0000.0000.00{{ '%02d' % ROUTER_NUMBER }}.00
 segment-routing srv6
  locator MAIN
 exit
exit
!
segment-routing
 srv6
  encapsulation
   source-address fd00:1:{{ ROUTER_NUMBER }}::
  exit
  locators
   locator MAIN
    prefix fd00:1:{{ ROUTER_NUMBER }}::/48
    behavior usid
    format usid-f3216
   exit
   !
  exit
  !
 exit
 !
exit
!
end
"""

PE_INTERFACE_TEMPLATE = """\
!
interface eth0
 ip address 192.168.255.{{ ROUTER_NUMBER }} peer 192.168.255.1/32
 ip router isis 1
 ipv6 router isis 1
 isis network point-to-point
exit
!
interface eth1
 ip address 192.168.255.{{ ROUTER_NUMBER }} peer 192.168.255.2/32
 ip router isis 1
 ipv6 router isis 1
 isis network point-to-point
exit
!
interface eth2
 description TO CE ROUTER
 ip address 10.0.{{ ROUTER_NUMBER }}.1/24
exit
!
"""

P_INTERFACE_TEMPLATE = """\
!
interface eth0
 ip address 192.168.255.{{ ROUTER_NUMBER }} peer 192.168.255.11/32
 ip router isis 1
 ipv6 router isis 1
 isis network point-to-point
exit
!
interface eth1
 ip address 192.168.255.{{ ROUTER_NUMBER }} peer 192.168.255.12/32
 ip router isis 1
 ipv6 router isis 1
 isis network point-to-point
exit
!
interface eth2
 ip address 192.168.255.{{ ROUTER_NUMBER }} peer 192.168.255.13/32
 ip router isis 1
 ipv6 router isis 1
 isis network point-to-point
exit
!
interface eth3
 ip address 192.168.255.{{ ROUTER_NUMBER }} peer 192.168.255.14/32
 ip router isis 1
 ipv6 router isis 1
 isis network point-to-point
exit
!
"""

CE_CONFIG_TEMPLATE = """\
hostname {{ HOSTNAME }}
!
interface eth0
 ip address {{ PE_CE_ADDR }}
exit
!

"""



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

        # 指定されたimage_definitionが存在するか確認して、なければ終了する
        image_defs = client.definitions.image_definitions()
        image_def_ids = [img['id'] for img in image_defs]
        if IMAGE_DEFINITION not in image_def_ids:
            logger.error(f"Specified image definition '{IMAGE_DEFINITION}' not found in CML.")
            return 1

        # ラボを新規作成
        lab = client.create_lab(title=LAB_NAME)

        # (X, Y)座標
        x = 0
        y = 0
        x_grid_width = 200
        y_grid_width = 160

        # Jinja2のTemplateをインスタンス化する
        config_template = Template(CONFIG_TEMPLATE)
        pe_interface_template = Template(PE_INTERFACE_TEMPLATE)
        p_interface_template = Template(P_INTERFACE_TEMPLATE)

        # templateに渡すコンテキストオブジェクト
        template_context = {
            "HOSTNAME": "R",
            "ROUTER_NUMBER": 1,
            "INTERFACES": ""
        }

        # Pルータを格納しておくリスト
        p_routers = []

        # PEルータを格納しておくリスト
        pe_routers = []

        # Pルータを2個作る
        for router_number in range(1, 3):
            node_name = f"P{router_number}"
            node = lab.create_node(node_name, NODE_DEFINITION, x, y)

            # インタフェースを4個作成する
            for _ in range(4):
                node.create_interface(_, wait=True)

            # 起動イメージを指定する
            node.image_definition = IMAGE_DEFINITION

            # スマートタグを設定
            # node.add_tag(tag="SRv6")

            # pattyのタグを設定
            # 例 serial:5001
            node.add_tag(tag=f"serial:{SERIAL_PORT + router_number}")

            # Pルータの設定を作る
            template_context["HOSTNAME"] = node_name
            template_context["ROUTER_NUMBER"] = router_number
            template_context["INTERFACES"] = p_interface_template.render(template_context)
            config_text = config_template.render(template_context)

            # FRRに設定するファイル一式
            frr_configurations = [
                {
                    'name': 'frr.conf',
                    'content': config_text
                },
                {
                    'name': 'protocols',
                    'content': PROTOCOLS_TEXT
                }
            ]

            # ノードに設定を適用する
            node.configuration = frr_configurations

            # リストに追加しておく
            p_routers.append(node)

            y += y_grid_width


        # 次はPEルータを作るのでX座標をPルータの左側に、Y座標を0に設定する
        x = -x_grid_width
        y = 0

        # PEルータを4個作る
        for router_number in range(11, 15):
            node_name = f"PE{router_number}"
            node = lab.create_node(node_name, NODE_DEFINITION, x, y)

            # インタフェースを4個作成する
            for _ in range(4):
                node.create_interface(_, wait=True)

            # 起動イメージを指定する
            node.image_definition = IMAGE_DEFINITION

            # スマートタグを設定
            # node.add_tag(tag="SRv6")

            # pattyのタグを設定
            # 例 serial:5001
            node.add_tag(tag=f"serial:{SERIAL_PORT + router_number}")

            # PEルータの設定を作る
            template_context["HOSTNAME"] = node_name
            template_context["ROUTER_NUMBER"] = router_number
            template_context["INTERFACES"] = pe_interface_template.render(template_context)
            config_text = config_template.render(template_context)

            # FRRに設定するファイル一式
            frr_configurations = [
                {
                    'name': 'frr.conf',
                    'content': config_text
                },
                {
                    'name': 'protocols',
                    'content': PROTOCOLS_TEXT
                }
            ]

            # ノードに設定を適用する
            node.configuration = frr_configurations

            # リストに追加しておく
            pe_routers.append(node)

            # 次のノードの座標を計算する
            y += y_grid_width
            if router_number == 12:
                y = 0
                x += x_grid_width * 2

        # 各PEルータからP1に接続する
        for index, pe_router in enumerate(pe_routers):
            # PEルータのeth0を取り出す
            pe_interface = pe_router.get_interface_by_label("eth0")
            # P1ルータのeth0～3を順に取り出す
            p_interface = p_routers[0].get_interface_by_label(f"eth{index}")
            # 接続する
            lab.create_link(pe_interface, p_interface, wait=True)

        # 各PEルータからP2に接続する
        for index, pe_router in enumerate(pe_routers):
            # PEルータのeth1を取り出す
            pe_interface = pe_router.get_interface_by_label("eth1")
            # P2ルータのeth0～3を順に取り出す
            p_interface = p_routers[1].get_interface_by_label(f"eth{index}")
            # 接続する
            lab.create_link(pe_interface, p_interface, wait=True)

        # SRv6ドメインがわかるように、スマートアノテーションを作る
        lab.create_smart_annotation('SRv6', p_routers + pe_routers, **{
            'fill_color': "#F3EAEAFF",
            'border_color': '#F3EAEAFF'
        })


        # CEルータ用のテンプレート
        ce_config_template = Template(CE_CONFIG_TEMPLATE)

        # CE101を作る
        pe11 = pe_routers[0]
        ce101 = lab.create_node("CE101", NODE_DEFINITION, pe11.x - x_grid_width, pe11.y, wait=True)
        ce101.image_definition = IMAGE_DEFINITION
        ce101.add_tag(tag=f"serial:{SERIAL_PORT + 101}")
        # インタフェースを4個作成する
        for _ in range(4):
            ce101.create_interface(_, wait=True)
        # CEルータの設定を作る
        ce101.configuration = [{
            'name': 'frr.conf',
            'content': ce_config_template.render({
                "HOSTNAME": "CE101",
                "PE_CE_ADDR": "10.0.11.101/24"
            })
        }]
        # CEルータのeth0とPEのeth2を接続する
        ce101_eth0 = ce101.get_interface_by_label("eth0")
        pe11_eth2 = pe11.get_interface_by_label("eth2")
        lab.create_link(ce101_eth0, pe11_eth2, wait=True)

        # CE102を作る
        pe12 = pe_routers[1]
        ce102 = lab.create_node("CE102", NODE_DEFINITION, pe12.x - x_grid_width, pe12.y, wait=True)
        ce102.image_definition = IMAGE_DEFINITION
        ce102.add_tag(tag=f"serial:{SERIAL_PORT + 102}")
        # インタフェースを4個作成する
        for _ in range(4):
            ce102.create_interface(_, wait=True)
        # CEルータの設定を作る
        ce102.configuration = [{
            'name': 'frr.conf',
            'content': ce_config_template.render({
                "HOSTNAME": "CE102",
                "PE_CE_ADDR": "10.0.12.102/24"
            })
        }]
        # CEルータのeth0とPEのeth2を接続する
        ce102_eth0 = ce102.get_interface_by_label("eth0")
        pe12_eth2 = pe12.get_interface_by_label("eth2")
        lab.create_link(ce102_eth0, pe12_eth2, wait=True)

        # CE103を作る
        pe13 = pe_routers[2]
        ce103 = lab.create_node("CE103", NODE_DEFINITION, pe13.x + x_grid_width, pe13.y, wait=True)
        ce103.image_definition = IMAGE_DEFINITION
        ce103.add_tag(tag=f"serial:{SERIAL_PORT + 103}")
        # インタフェースを4個作成する
        for _ in range(4):
            ce103.create_interface(_, wait=True)
        # CEルータの設定を作る
        ce103.configuration = [{
            'name': 'frr.conf',
            'content': ce_config_template.render({
                "HOSTNAME": "CE103",
                "PE_CE_ADDR": "10.0.13.103/24"
            })
        }]
        ce103_eth0 = ce103.get_interface_by_label("eth0")
        pe13_eth2 = pe13.get_interface_by_label("eth2")
        lab.create_link(ce103_eth0, pe13_eth2, wait=True)

        # CE104を作る
        pe14 = pe_routers[3]
        ce104 = lab.create_node("CE104", NODE_DEFINITION, pe14.x + x_grid_width, pe14.y, wait=True)
        ce104.image_definition = IMAGE_DEFINITION
        ce104.add_tag(tag=f"serial:{SERIAL_PORT + 104}")
        # インタフェースを4個作成する
        for _ in range(4):
            ce104.create_interface(_, wait=True)
        ce104.configuration = [{
            'name': 'frr.conf',
            'content': ce_config_template.render({
                "HOSTNAME": "CE104",
                "PE_CE_ADDR": "10.0.14.104/24"
            })
        }]
        ce104_eth0 = ce104.get_interface_by_label("eth0")
        pe14_eth2 = pe14.get_interface_by_label("eth2")
        lab.create_link(ce104_eth0, pe14_eth2, wait=True)


        # アノテーションを作成する
        text_content = 'FRR SRv6 uSID'
        lab.create_annotation('text', **{
            'border_color': '#00000000',
            'border_style': '',
            'rotation': 0,
            'text_bold': False,
            'text_content': text_content,
            'text_font': 'monospace',
            'text_italic': False,
            'text_size': 20,
            'text_unit': 'pt',
            'thickness': 1,
            'x1': -400.0,
            'y1': -160.0,
            'z_index': 0
        })

        text_content = 'fd00:0001: {{ 00 router-number }}/48'
        lab.create_annotation('text', **{
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
            'x1': -400.0,
            'y1': -120.0,
            'z_index': 1
        })

        text_content = '49.0001 . 0000.0000.00{{ router-number }} . 00'
        lab.create_annotation('text', **{
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
            'x1': -400.0,
            'y1': -80.0,
            'z_index': 2
        })

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
