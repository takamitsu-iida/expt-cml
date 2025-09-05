#!/usr/bin/env python

###########################################################

#
# 作成するラボの情報
#

# ラボの名前、既存で同じタイトルのラボがあれば削除してから作成する
LAB_NAME = "FRR OpenFabric"

# このラボで使うシリアルポートの開始番号
SERIAL_PORT = 7000

# ノード定義
NODE_DEFINITION = "ubuntu"

# イメージ定義
IMAGE_DEFINITION = "ubuntu-24-04-20250503-frr"

# ノードにつけるタグ
NODE_TAG = "serial:6000"

# Ubuntuノードに与える初期設定のテンプレートのコンテキストで使うホスト名
UBUNTU_HOSTNAME = "ubuntu-0"

# Ubuntuノードに与える初期設定のテンプレートのコンテキストで使うユーザ名
UBUNTU_USERNAME = "cisco"

# Ubuntuノードに与える初期設定のテンプレートのコンテキストで使うパスワード
UBUNTU_PASSWORD = "cisco"

# Ubuntuノードに与える初期設定のテンプレートのコンテキストで使うSSH公開鍵
UBUNTU_SSH_PUBLIC_KEY = "AAAAB3NzaC1yc2EAAAADAQABAAABgQDdnRSDloG0LXnwXEoiy5YU39Sm6xTfvcpNm7az6An3rCfn2QC2unIWyN6sFWbKurGoZtA6QdKc8iSPvYPMjrS6P6iBW/cUJcoU8Y8BwUCnK33iKdCfkDWVDdNGN7joQ6DejhKTICTmcBJmwN9utJQVcagCO66Y76Xauub5WHs9BdAvpr+FCQh0eEQ7WZF1BQvH+bPXGmRxPQ8ViHvlUdgsVEq6kv9e/plh0ziXmkBXAw0bdquWu1pArX76jugQ4LXEJKgmQW/eBNiDgHv540nIH5nPkJ7OYwr8AbRCPX52vWhOr500U4U9n2FIVtMKkyVLHdLkx5kZ+cRJgOdOfMp8vaiEGI6Afl/q7+6n17SpXpXjo4G/NOE/xnjZ787jDwOkATiUGfCqLFaITaGsVcUL0vK2Nxb/tV5a2Rh1ELULIzPP0Sw5X2haIBLUKmQ/lmgbUDG6fqmb1z8XTon1DJQSLQXiojinknBKcMH4JepCrsYTAkpOsF6Y98sZKNIkAqU= iida@FCCLS0008993-00"

###########################################################

# ubuntuに設定するcloud-init.yamlのJinja2テンプレート
UBUNTU_CONFIG = """#cloud-config
hostname: {{ HOSTNAME }}
manage_etc_hosts: True
system_info:
  default_user:
    name: {{ USERNAME }}
password: {{ PASSWORD }}
chpasswd: { expire: False }
ssh_pwauth: True
ssh_authorized_keys:
  - ssh-rsa {{ SSH_PUBLIC_KEY }}

timezone: Asia/Tokyo
locale: ja_JP.utf8

write_files:
  # overwrite 60-cloud-init.yaml
  - path: /etc/netplan/60-cloud-init.yaml
    permissions: '0600'
    owner: root:root
    content: |-
      network:
        version: 2
        renderer: networkd
        ethernets:
          ens2:
            dhcp4: false
            dhcp6: false
            link-local: []
            addresses:
                - fe80::{{ ROUTER_ID }}/64
          ens3:
            dhcp4: false
            dhcp6: false
            link-local: []
            addresses:
                - fe80::{{ ROUTER_ID }}/64
          ens4:
            dhcp4: false
            dhcp6: false
            link-local: []
            addresses:
                - fe80::{{ ROUTER_ID }}/64
          ens5:
            dhcp4: false
            dhcp6: false
            link-local: []
            addresses:
                - fe80::{{ ROUTER_ID }}/64
          ens6:
            dhcp4: false
            dhcp6: false
            link-local: []
            addresses:
                - fe80::{{ ROUTER_ID }}/64
          ens7:
            dhcp4: false
            dhcp6: false
            link-local: []
            addresses:
                - fe80::{{ ROUTER_ID }}/64
          ens8:
            dhcp4: false
            dhcp6: false
            link-local: []
            addresses:
                - fe80::{{ ROUTER_ID }}/64
          ens9:
            dhcp4: false
            dhcp6: false
            link-local: []
            addresses:
                - fe80::{{ ROUTER_ID }}/64

  - path: /etc/frr/frr.conf
    content: |-
{{ FRR_CONF }}

runcmd:

  # enable frr fabricd
  - sed -i -e "s/^fabricd=no/fabricd=yes/" /etc/frr/daemons

  - reboot
"""

# FRRの設定テンプレート
FRR_CONFIG = """
!
frr defaults traditional
hostname {{ HOSTNAME }}
log syslog informational
service integrated-vtysh-config
{%- for i in range(2, 10) %}
!
interface ens{{ i }}
 ip router openfabric 1
 ipv6 address fe80::{{ IPv6_ROUTER_ID }}/64
 ipv6 router openfabric 1
exit
{%- endfor %}
!
interface lo
 ip address 192.168.255.{{ IPv4_ROUTER_ID }}/32
 ip router openfabric 1
 ipv6 address 2001:db8::{{ IPv6_ROUTER_ID }}/128
 ipv6 router openfabric 1
 openfabric passive
exit
!
router openfabric 1
 net 49.0000.0000.00{{ IPv6_ROUTER_ID }}.00
 fabric-tier {{ TIER }}
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


    def indent_string(text):
        """文字列の行頭にスペースを挿入する"""
        lines = text.splitlines()  # 文字列を改行で分割
        indented_lines = ["      " + line for line in lines]  # 各行の先頭にスペース4個を追加
        return "\n".join(indented_lines)  # 改行で連結して返す


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

        # Jinja2のTemplateをインスタンス化する
        template = Template(UBUNTU_CONFIG)

        # templateに渡すコンテキストオブジェクトを作成する
        lab_context = {
            "HOSTNAME": "",
            "USERNAME": UBUNTU_USERNAME,
            "PASSWORD": UBUNTU_PASSWORD,
            "SSH_PUBLIC_KEY": UBUNTU_SSH_PUBLIC_KEY,
            "ROUTER_ID": "",
            "FRR_CONF": ""
        }

        # Ubuntu上のFRRの設定テンプレート
        frr_template = Template(FRR_CONFIG)
        frr_context = {
            "HOSTNAME": "R",
            "IPv4_ROUTER_ID": "",
            "IPv6_ROUTER_ID": "",
            "TIER": "0",
        }

        # ルータを区別するための番号
        router_number = 1

        # openfabricの用語では末端に近いところからT0、T1の順で呼ぶ
        # ここでは３階層のネットワークを作るのでT0, T1, T2を作る。

        # 作成するt2ノードを格納しておくリスト
        t2_nodes = []

        # T2のUbuntuを3個作る
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

            # その名前でUbuntuをインスタンス化する
            node = lab.create_node(node_name, 'ubuntu', x, y)

            # 初期状態はインタフェースが存在しないので追加する
            # Ubuntuのslot番号範囲は0-7なので、最大8個のNICを作れる
            # slot番号はインタフェース名ではない
            # OSから見えるインタフェース目はens2, ens3, ...ens9となる
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
            frr_context["HOSTNAME"] = node_name
            frr_context["IPv4_ROUTER_ID"] = str(router_number)
            frr_context["IPv6_ROUTER_ID"] = "{:0=2}".format(router_number)
            frr_context["TIER"] = "2"
            frr_config = frr_template.render(frr_context)
            frr_config = indent_string(frr_config)

            # nodeに適用するcloud-init設定を作る
            lab_context["HOSTNAME"] = node_name
            lab_context["ROUTER_ID"] = router_number
            lab_context["FRR_CONF"] = frr_config

            # ノードに設定する
            node.configuration = template.render(lab_context)

            # リストに追加する
            t2_nodes.append(node)

            # ルータを作ったので一つ数字を増やす
            router_number += 1

        # 続いてクラスタを2個作る
        x += grid_width
        y = 0
        num_clusters = 2
        for i in range(num_clusters):

            # クラスタ内のスパインルータ（T1ルータ）を格納するリスト
            t1_nodes = []

            # クラスタ内にT1ルータを2個作る
            for j in range(2):
                node_name = f"R{router_number}"
                node = lab.create_node(node_name, 'ubuntu', x, y)
                y += grid_width

                # NICを8個追加
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
                frr_context["IPv4_ROUTER_ID"] = str(router_number)
                frr_context["IPv6_ROUTER_ID"] = "{:0=2}".format(router_number)
                frr_context["TIER"] = "1"
                frr_config = frr_template.render(frr_context)
                frr_config = indent_string(frr_config)

                # cloud-init設定
                lab_context["HOSTNAME"] = node_name
                lab_context["ROUTER_ID"] = router_number
                lab_context["FRR_CONF"] = frr_config
                node.configuration = template.render(lab_context)

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
                node = lab.create_node(node_name, 'ubuntu', t0_x, t0_y)
                t0_x += grid_width

                # NICを8個追加
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
                frr_context["IPv4_ROUTER_ID"] = str(router_number)
                frr_context["IPv6_ROUTER_ID"] = "{:0=2}".format(router_number)
                frr_context["TIER"] = "0"
                frr_config = frr_template.render(frr_context)
                frr_config = indent_string(frr_config)

                # 設定
                lab_context["HOSTNAME"] = node_name
                lab_context["ROUTER_ID"] = router_number
                lab_context["FRR_CONF"] = frr_config
                node.configuration = template.render(lab_context)

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
