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
import subprocess
import sys
import tempfile
import time

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

def create_router_config_1() -> str:

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
system domain-name iida.local
system login-banner "ArcOS (c) Arrcus, Inc."
system clock timezone-name Asia/Tokyo
system ssh-server enable true
system ssh-server permit-root-login true
system cli commit-message true
system netconf-server enable true
system netconf-server transport ssh enable true
system netconf-server transport ssh timeout 60
system restconf-server enable true
system dns server-group management
 server 192.168.254.100
 !
!
system ntp listen-interface ma1
system ntp server 192.168.254.100
 iburst true
!
system grpc-server enable true
system grpc-server transport-security false
system grpc-server connections management
 port 9339
!
system aaa authentication admin-user admin-password $6$cY9EPmy0Nms9aP1k$Z2HzLTQGLpu5mlYx/dw0rWlsXM.Y3D56m7OBSkNWdpEuJC/Htnk36jPDGZ8yqNgsOzWbo3qQDEcxz8LJ3rnim0
system aaa authentication user admin
 password $6$vNZR.uPPRaj9w2YE$fT8DCzLZ8yyad7UleD/lkRRwo038UD/j1JM0.QIAlZ9IG.2QscG7BnO7KALU6O8BGtjtWAQgPWpqlkCsm/IVu/
 role     SYSTEM_ROLE_ADMIN
!
system aaa authentication user cisco
 password $6$3eknMONEms3fQwFn$/bdFD9rIta5JPFzyDMBsWsJxxAyBQcpK8QCokRc1aAP3puQ9EZvLOMoNpKNhf63QT4x5bytzOfaH1jUBNnBYC0
 role     SYSTEM_ROLE_ADMIN
!
system icmp source-interface loopback0
 network-instance default
!
system rib IPV6
!
system rib IPV4
!
system snmp-server enable true
system snmp-server protocol-version [ V2C ]
system snmp-server network-instance management
system snmp-server contact takamitsu-iida
system snmp-server location "Kamioooka Yokohama JP"
system snmp-server community public
interface ma1
 type    ethernetCsmacd
 mtu     1500
 enabled true
 subinterface 0
  ipv6 router-advertisement suppress true
 exit
!
{% for iface_num in range(1,5) -%}
interface swp{{ iface_num }}
 type    ethernetCsmacd
 mtu     3000
 enabled true
 subinterface 0
  ipv6 enabled true
  ipv6 router-advertisement suppress true
  ipv4 enabled false
  enabled true
 exit
!
{% endfor -%}
interface loopback0
 type    softwareLoopback
 mtu     3000
 enabled true
 subinterface 0
  ipv6 enabled true
  ipv6 address 2001:db8:ffff::{{ rid }}
   prefix-length 128
  exit
  ipv4 enabled true
  ipv4 address 10.0.255.{{ rid }}
   prefix-length 32
  exit
  enabled true
 exit
!
network-instance default
 resolve-dns-in-network-instance management
 protocol BGP MAIN
  global as           65000
  global router-id    10.0.255.{{ rid }}
  global cluster-id   0.0.0.1
  global graceful-restart enabled true
  global afi-safi L3VPN_IPV6_UNICAST
  !
  global afi-safi L3VPN_IPV4_UNICAST
  !
  global srv6 locator MAIN
  {% if rid == 1 -%}
  neighbor 2001:db8:ffff::2
  {% else -%}
  neighbor 2001:db8:ffff::1
  {% endif -%}
   peer-as 65000
   transport local-address 2001:db8:ffff::{{ rid }}
   afi-safi L3VPN_IPV6_UNICAST
    extended-nexthop enable true
    exit
   !
   afi-safi L3VPN_IPV4_UNICAST
    extended-nexthop enable true
    exit
   !
   exit
  !
  {% for neighbor_id in range(11, 15) -%}
  neighbor 2001:db8:ffff::{{ neighbor_id }}
   peer-group pe
   exit
  !
  {% endfor -%}
  peer-group pe
   peer-as 65000
   transport local-address 2001:db8:ffff::{{ rid }}
   route-reflector route-reflector-client true
   afi-safi L3VPN_IPV6_UNICAST
    extended-nexthop enable true
    exit
   !
   afi-safi L3VPN_IPV4_UNICAST
    extended-nexthop enable true
    exit
   !
  !
 !
 protocol ISIS MAIN
  global net [ 49.0000.0000.0000.000{{ rid }}.00 ]
  global graceful-restart enabled true
  global af IPV6 UNICAST
   enabled true
   exit
  !
  global af IPV4 UNICAST
   enabled false
   exit
  !
  global srv6 enabled true
  global srv6 locator MAIN
  !
  level 1
   enabled true
   exit
  !
  level 2
   enabled true
   exit
  !
  {% for iface_num in range(1,5) -%}
  interface swp{{ iface_num }}
   enabled      true
   network-type POINT_TO_POINT
   af IPV6 UNICAST
    enabled true
   !
   af IPV4 UNICAST
    enabled false
   !
   level 1
    enabled true
    exit
   !
   level 2
    enabled false
    exit
   !
   exit
  !
  {% endfor -%}
  interface loopback0
   enabled true
   passive true
   af IPV6 UNICAST
    enabled true
   !
   af IPV4 UNICAST
    enabled false
   !
   level 1
    enabled true
    exit
   !
   level 2
    enabled false
    exit
   !
   exit
  !
 !
 srv6 locator MAIN
  locator-node-length 16
  prefix              fd00:0:0:{{ rid }}::/64
 !
!
network-instance management
 interface ma1
 !
!
lldp interface ma1
!
lldp interface swp1
!
lldp interface swp2
!
lldp interface swp3
!
lldp interface swp4
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

    PE_CONFIG_J2 = \
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
system hostname PE{{ rid }}
system domain-name iida.local
system login-banner "ArcOS (c) Arrcus, Inc."
system clock timezone-name Asia/Tokyo
system ssh-server enable true
system ssh-server permit-root-login true
system cli commit-message true
system netconf-server enable true
system netconf-server transport ssh enable true
system netconf-server transport ssh timeout 60
system restconf-server enable true
system dns server-group management
 server 192.168.254.100
 !
!
system ntp listen-interface ma1
system ntp server 192.168.254.100
 iburst true
!
system grpc-server enable true
system grpc-server transport-security false
system grpc-server connections management
 port 9339
!
system aaa authentication admin-user admin-password $6$cY9EPmy0Nms9aP1k$Z2HzLTQGLpu5mlYx/dw0rWlsXM.Y3D56m7OBSkNWdpEuJC/Htnk36jPDGZ8yqNgsOzWbo3qQDEcxz8LJ3rnim0
system aaa authentication user admin
 password $6$vNZR.uPPRaj9w2YE$fT8DCzLZ8yyad7UleD/lkRRwo038UD/j1JM0.QIAlZ9IG.2QscG7BnO7KALU6O8BGtjtWAQgPWpqlkCsm/IVu/
 role     SYSTEM_ROLE_ADMIN
!
system aaa authentication user cisco
 password $6$3eknMONEms3fQwFn$/bdFD9rIta5JPFzyDMBsWsJxxAyBQcpK8QCokRc1aAP3puQ9EZvLOMoNpKNhf63QT4x5bytzOfaH1jUBNnBYC0
 role     SYSTEM_ROLE_ADMIN
!
system icmp source-interface loopback0
 network-instance default
!
system rib IPV6
!
system rib IPV4
!
system snmp-server enable true
system snmp-server protocol-version [ V2C ]
system snmp-server network-instance management
system snmp-server contact takamitsu-iida
system snmp-server location "Kamioooka Yokohama JP"
system snmp-server community public
interface ma1
 type    ethernetCsmacd
 mtu     1500
 enabled true
 subinterface 0
  ipv6 router-advertisement suppress true
 exit
!
{% for iface_num in range(1,3) -%}
interface swp{{ iface_num }}
 type    ethernetCsmacd
 mtu     3000
 enabled true
 subinterface 0
  ipv6 enabled true
  ipv6 router-advertisement suppress true
  ipv4 enabled false
 exit
!
{% endfor -%}
{% for iface_num in range(3,5) -%}
interface swp{{ iface_num }}
 type    ethernetCsmacd
 mtu     3000
 enabled true
!
{% endfor -%}
interface swp3
 type    ethernetCsmacd
 mtu     3000
 enabled true
 subinterface 0
  ipv4 enabled true
  ipv4 address 172.16.{{ rid }}.1
   prefix-length 24
  exit
  enabled true
 exit
!
interface loopback0
 type    softwareLoopback
 mtu     3000
 enabled true
 subinterface 0
  ipv6 enabled true
  ipv6 address 2001:db8:ffff::{{ rid }}
   prefix-length 128
  exit
  ipv4 enabled true
  ipv4 address 10.0.255.{{ rid }}
   prefix-length 32
  exit
  enabled true
 exit
!
network-instance default
 resolve-dns-in-network-instance management
 protocol BGP MAIN
  global as           65000
  global router-id    10.0.255.{{ rid }}
  global graceful-restart enabled true
  global afi-safi L3VPN_IPV6_UNICAST
  !
  global afi-safi L3VPN_IPV4_UNICAST
  !
  global srv6 locator MAIN
  neighbor 2001:db8:ffff::1
   peer-group rr
   exit
  !
  neighbor 2001:db8:ffff::2
   peer-group rr
   exit
  !
  peer-group rr
   peer-as 65000
   transport local-address 2001:db8:ffff::{{ rid }}
   afi-safi L3VPN_IPV6_UNICAST
    extended-nexthop enable true
    exit
   !
   afi-safi L3VPN_IPV4_UNICAST
    extended-nexthop enable true
    exit
   !
  !
 !
 protocol ISIS MAIN
  global net [ 49.0000.0000.0000.00{{ rid }}.00 ]
  global graceful-restart enabled true
  global af IPV6 UNICAST
   enabled true
   exit
  !
  global af IPV4 UNICAST
   enabled false
   exit
  !
  global srv6 enabled true
  global srv6 locator MAIN
  !
  level 1
   enabled true
   exit
  !
  level 2
   enabled false
   exit
  !
  {% for iface_num in range(1,3) -%}
  interface swp{{ iface_num }}
   enabled      true
   network-type POINT_TO_POINT
   af IPV6 UNICAST
    enabled true
   !
   af IPV4 UNICAST
    enabled false
   !
   level 1
    enabled true
    exit
   !
   level 2
    enabled false
    exit
   !
   exit
  !
  {% endfor -%}
  interface loopback0
   enabled true
   passive true
   af IPV6 UNICAST
    enabled true
   !
   af IPV4 UNICAST
    enabled false
   !
   level 1
    enabled true
    exit
   !
   level 2
    enabled false
    exit
   !
   exit
  !
 !
 srv6 locator MAIN
  locator-node-length 16
  prefix              fd00:0:0:{{ rid }}::/64
 !
!
network-instance management
 interface ma1
 !
!
network-instance vrf-1
 type L3VRF
 table-connection DIRECTLY_CONNECTED BGP IPV4
 !
 interface swp3
 !
 protocol BGP vrf-1
  global router-id    10.0.255.{{ rid }}
  global route-distinguisher 10.0.25.{{ rid }}:1
  global sid-allocation-mode INSTANCE_SID
  global afi-safi IPV4_UNICAST
   graceful-restart enabled true
   network 172.16.{{ rid }}.0/24
   !
   rt-afi-safi L3VPN_IPV4_UNICAST
    route-target 65000:1 both
     exit
    !
    exit
   !
  !
  global afi-safi IPV6_UNICAST
  !
  global srv6 locator MAIN
 !
!
lldp interface ma1
!
lldp interface swp1
!
lldp interface swp2
!
lldp interface swp3
!
lldp interface swp4
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
    pe_config_template = Template(PE_CONFIG_J2)

    return {
        "P1_CONFIG": p_config_template.render({ "rid": 1 }),
        "P2_CONFIG": p_config_template.render({ "rid": 2 }),
        "PE11_CONFIG": pe_config_template.render({ "rid": 11 }),
        "PE12_CONFIG": pe_config_template.render({ "rid": 12 }),
        "PE13_CONFIG": pe_config_template.render({ "rid": 13 }),
        "PE14_CONFIG": pe_config_template.render({ "rid": 14 }),
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
            if not iface.connected:
                ma_switch_iface = iface
                break

        if ma_switch_iface is None:
            logger.error(f"No available interface on MA switch '{MA_SWITCH_LABEL}' to connect to node '{node.label}'")
            continue

        # ノードのma1インタフェースとMAスイッチのインタフェースを接続する
        lab.create_link(ma_iface, ma_switch_iface, wait=True)


def create_nodes_1(lab: Lab) -> list[Node]:
    #
    # この構成のラボを作ります。
    #
    # CE111----PE11----P1----PE13----CE113
    #                \/    \/
    #                /\    /\
    # CE112----PE12----P2----PE14----CE114
    #

    # 同じラベルのノードは作成できないので、作る前に削除する
    def delete_node(label: str) -> None:
        try:
            node = lab.get_node_by_label(label)
            if node.is_booted:
                node.stop(wait=True)
            node.wipe(wait=True)
            node.remove()
        except NodeNotFound:
            pass

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

    # VPNの領域をレクタングルアノテーションを作成する
    create_rectangle_annotation(lab, {'x1': -520.0, 'y1': 120.0, 'x2': 280.0, 'y2': 80.0, 'z_index': 1})
    create_rectangle_annotation(lab, {'x1': -520.0, 'y1': 280.0, 'x2': 280.0, 'y2': 80.0, 'z_index': 1})
    create_rectangle_annotation(lab, {'x1': 240.0, 'y1': 120.0, 'x2': 280.0, 'y2': 80.0, 'z_index': 1})
    create_rectangle_annotation(lab, {'x1': 240.0, 'y1': 280.0, 'x2': 280.0, 'y2': 80.0, 'z_index': 1})

    # CEルータのアドレスを示すテキストアノテーションを作成する
    create_text_annotation(lab, "172.16.11.0/24", {'x1': -440.0, 'y1': 120.0, 'z_index': 2})
    create_text_annotation(lab, "172.16.12.0/24", {'x1': -440.0, 'y1': 280.0, 'z_index': 2})
    create_text_annotation(lab, "172.16.13.0/24", {'x1': 320.0, 'y1': 120.0, 'z_index': 2})
    create_text_annotation(lab, "172.16.14.0/24", {'x1': 320.0, 'y1': 280.0, 'z_index': 2})

    # ルータを作成する
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
        delete_node(f"P{rid}")
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
        delete_node(f"PE{rid}")
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
            ma_iface.mac_address = f"52:54:00:00:00:{rid:02d}"

        # Y座標を下にずらす
        y_pos += y_grid_width

        # PEノードをリストに追加
        pe_nodes.append(node)

        # CEルータをPEの左側に作る
        #
        # CE111----PE11
        #
        # CE112----PE12
        #
        delete_node(f"CE1{rid}")
        ce = lab.create_node(f"CE1{rid}", "iol-xe", node.x - x_grid_width, node.y, wait=True)
        ce.add_tag(tag=f"serial:61{rid}")
        for _ in range(4):
            ce.create_interface(_, wait=True)
        ce.configuration = [{
            'name': 'ios_config.txt',
            'content': \
f"""
!
hostname CE1{rid}
!
clock timezone JST 9 0
!
interface Ethernet0/0
 ip address 172.16.{rid}.100 255.255.255.0
 no shutdown
!
ip route 0.0.0.0 0.0.0.0 172.16.{rid}.1
!
""".strip()
        }]

        ce_eth = ce.get_interface_by_label("Ethernet0/0")
        pe_eth = node.get_interface_by_label("swp3")
        lab.create_link(ce_eth, pe_eth, wait=True)


    # 右側にあるPE13, PE14ノードを作る
    x_pos = x_grid_width
    y_pos = y_grid_width
    for rid in [13, 14]:
        delete_node(f"PE{rid}")
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
            ma_iface.mac_address = f"52:54:00:00:00:{rid:02d}"

        # Y座標を下にずらす
        y_pos += y_grid_width

        # PEノードをリストに追加
        pe_nodes.append(node)

        # CEルータをPEの右側に作る
        #
        # PE13----CE113
        #
        # PE14----CE114
        #
        delete_node(f"CE1{rid}")
        ce = lab.create_node(f"CE1{rid}", "iol-xe", node.x + x_grid_width, node.y, wait=True)
        ce.add_tag(tag=f"serial:61{rid}")
        for _ in range(4):
            ce.create_interface(_, wait=True)
        ce.configuration = [{
            'name': 'ios_config.txt',
            'content': \
f"""
!
hostname CE1{rid}
!
clock timezone JST 9 0
!
interface Ethernet0/0
 ip address 172.16.{rid}.100 255.255.255.0
 no shutdown
!
ip route 0.0.0.0 0.0.0.0 172.16.{rid}.1
!
""".strip()
        }]
        ce_eth = ce.get_interface_by_label("Ethernet0/0")
        pe_eth = node.get_interface_by_label("swp3")
        lab.create_link(ce_eth, pe_eth, wait=True)

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

    existing_annotations = lab.annotations()

    for annotation in existing_annotations:
        if annotation.type == 'text' and annotation.text_content == text_content:
                return

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


def create_rectangle_annotation(lab: Lab, params: dict = None) -> None:

    existing_annotations = lab.annotations()

    for annotation in existing_annotations:
        if (annotation.type == 'rectangle' and
            annotation.x1 == params.get('x1', 0.0) and
            annotation.y1 == params.get('y1', 0.0) and
            annotation.x2 == params.get('x2', 0.0) and
            annotation.y2 == params.get('y2', 0.0)):
                return

    base_params = {
        'border_color': '#F5F8F8',
        'border_radius': 0,
        'border_style': '',
        'color': '#F5F8F8',
        'rotation': 0,
        'thickness': 1,
        'x1': 0.0,
        'y1': 0.0,
        'x2': 0.0,
        'y2': 0.0,
        'z_index': 1
    }
    if params:
        base_params.update(params)
    lab.create_annotation('rectangle', **base_params)


def get_lab_by_title(client: ClientLibrary, title: str) -> Lab | None:
    labs = client.find_labs_by_title(title)
    return labs[0] if labs else None


def start_lab(lab: Lab) -> None:
    # 状態にかかわらず起動する
    logger.info(f"Starting lab '{lab.title}'")
    lab.start(wait=True)
    logger.info(f"Lab '{lab.title}' started")


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

    configs = create_router_config_1()

    scp_to_jumphost(configs["P1_CONFIG"], "/srv/tftp/P1.cfg")
    scp_to_jumphost(configs["P2_CONFIG"], "/srv/tftp/P2.cfg")
    scp_to_jumphost(configs["PE11_CONFIG"], "/srv/tftp/PE11.cfg")
    scp_to_jumphost(configs["PE12_CONFIG"], "/srv/tftp/PE12.cfg")
    scp_to_jumphost(configs["PE13_CONFIG"], "/srv/tftp/PE13.cfg")
    scp_to_jumphost(configs["PE14_CONFIG"], "/srv/tftp/PE14.cfg")


def get_node_url_list(lab: Lab) -> list:
    urls = []
    if lab is None:
        return urls

    for node in lab.nodes():
        serial_tags = [ t for t in node.tags() if t.startswith('serial:') ]
        for tag in serial_tags:
            port = tag.split(':')[1]
            url = f"telnet://{CML_ADDRESS}:{port}"
            urls.append({'label': node.label, 'url': url})
            break  # 最初のserialタグだけ使う

    return urls


def generate_html_content(lab: Lab) -> str:
    """ノードのURLリストからHTMLコンテンツを生成する"""
    url_list = get_node_url_list(lab)

    html_content = \
"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CML Node Console Links</title>
    <style>
        body { font-family: Arial, sans-serif; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    </style>
</head>
<body>
    <h1>CML Node Console Links</h1>
    <br>
    <h2>P Routers</h2>
        <table>
            <thead>
                <tr><th>Label</th><th>URL</th></tr>
            </thead>
            <tbody>
            {% for item in url_list %}
                {% if item['label'].startswith('P') and not item['label'].startswith('PE') %}
                <tr>
                    <td>{{ item['label'] }}</td>
                    <td><a href="{{ item['url'] }}" target="_blank">{{ item['url'] }}</a></td>
                </tr>
                {% endif %}
            {% endfor %}
            </tbody>
        </table>
    <br>
    <h2>PE Routers</h2>
        <table>
            <thead>
                <tr><th>Label</th><th>URL</th></tr>
            </thead>
            <tbody>
            {% for item in url_list %}
                {% if item['label'].startswith('PE') %}
                <tr>
                    <td>{{ item['label'] }}</td>
                    <td><a href="{{ item['url'] }}" target="_blank">{{ item['url'] }}</a></td>
                </tr>
                {% endif %}
            {% endfor %}
            </tbody>
        </table>
    <br>
    <h2>CE Routers</h2>
        <table>
            <thead>
                <tr><th>Label</th><th>URL</th></tr>
            </thead>
            <tbody>
            {% for item in url_list %}
                {% if item['label'].startswith('CE') %}
                <tr>
                    <td>{{ item['label'] }}</td>
                    <td><a href="{{ item['url'] }}" target="_blank">{{ item['url'] }}</a></td>
                </tr>
                {% endif %}
            {% endfor %}
            </tbody>
        </table>
</body>
</html>
"""

    template = Template(html_content)
    html_content = template.render({ 'url_list': url_list })
    return html_content


def open_browser(html_content: str = '') -> None:
    """ブラウザでHTMLを表示"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, dir='/tmp') as tmp:
        tmp.write(html_content)
        tmp.flush()
        tmp_path = tmp.name

    try:
        result = subprocess.run(['wslpath', '-w', tmp_path], capture_output=True, text=True, check=True)
        windows_path = result.stdout.strip()

        subprocess.Popen(
            ['powershell.exe', '-Command', f'Start-Process "{windows_path}"'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        # ブラウザがファイルを読み込むまで待機
        time.sleep(10)

        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    except subprocess.CalledProcessError as e:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    except Exception as e:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


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
        parser.add_argument('--browser', action='store_true', default=False, help='Open browser to display console links')
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

        # 環境変数でバックグラウンドモードかチェック
        if os.getenv('_INTERNAL_BROWSER_MODE') == '1':
            html_content = generate_html_content(lab)
            open_browser(html_content=html_content)
            return

        if args.browser:
            # 環境変数でバックグラウンド実行を指示
            env = os.environ.copy()
            env['_INTERNAL_BROWSER_MODE'] = '1'

            subprocess.Popen(
                [sys.executable, __file__],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            logger.info("ブラウザ起動プロセスを開始しました（バックグラウンド実行）")
            return

    #
    # 実行
    #
    main()
