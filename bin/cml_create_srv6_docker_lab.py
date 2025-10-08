#!/usr/bin/env python

#
# SRv6を検証するためのラボを作成するスクリプトです
# FRR(Docker)を使って、SRv6の基本的な動作を確認できるラボを作成します
#

# スクリプトを引数無しで実行したときのヘルプに使うデスクリプション
LAB_DESCRIPTION = 'create srv6 docker lab'

# ラボの名前（既存で同じタイトルのラボがあれば削除してから作成します）
LAB_NAME = "Docker FRR SRv6"

# このラボで使うシリアルポートの開始番号
SERIAL_PORT = 5000

# ノード定義（Docker FRR）
NODE_DEFINITION = "frr-10-4"

# イメージ定義
IMAGE_DEFINITION = "frr-10-4"

# 管理用ubuntuイメージ定義
UBUNTU_IMAGE_DEFINITION = "ubuntu-24-04-20250503"

# 管理用ubuntuノードのホスト名
UBUNTU_HOSTNAME = "ubuntu"

# 管理用ubuntuノードのログイン名
UBUNTU_USERNAME = "cisco"

# 管理用ubuntuノードのパスワード
UBUNTU_PASSWORD = "cisco"

# id_rsa.pubの中身をそのまま貼り付けます
# SSH_PUBLIC_KEY = "YOUR_SSH_PUBLIC_KEY_HERE"
SSH_PUBLIC_KEY = "AAAAB3NzaC1yc2EAAAADAQABAAABgQDdnRSDloG0LXnwXEoiy5YU39Sm6xTfvcpNm7az6An3rCfn2QC2unIWyN6sFWbKurGoZtA6QdKc8iSPvYPMjrS6P6iBW/cUJcoU8Y8BwUCnK33iKdCfkDWVDdNGN7joQ6DejhKTICTmcBJmwN9utJQVcagCO66Y76Xauub5WHs9BdAvpr+FCQh0eEQ7WZF1BQvH+bPXGmRxPQ8ViHvlUdgsVEq6kv9e/plh0ziXmkBXAw0bdquWu1pArX76jugQ4LXEJKgmQW/eBNiDgHv540nIH5nPkJ7OYwr8AbRCPX52vWhOr500U4U9n2FIVtMKkyVLHdLkx5kZ+cRJgOdOfMp8vaiEGI6Afl/q7+6n17SpXpXjo4G/NOE/xnjZ787jDwOkATiUGfCqLFaITaGsVcUL0vK2Nxb/tV5a2Rh1ELULIzPP0Sw5X2haIBLUKmQ/lmgbUDG6fqmb1z8XTon1DJQSLQXiojinknBKcMH4JepCrsYTAkpOsF6Y98sZKNIkAqU= iida@FCCLS0008993-00"

# boot.shの設定
BOOT_SH_TEXT = """\
cp /root/deadman/deadman.conf /root/deadman/deadman.conf.bak
cat - << 'EOS' > /root/deadman/deadman.conf
P1      192.168.255.1
P2      192.168.255.2
PE11    192.168.255.11
PE12    192.168.255.12
PE13    192.168.255.13
PE14    192.168.255.14
---
P1      2001:db8:ffff::1
P2      2001:db8:ffff::2
PE11    2001:db8:ffff::11
PE12    2001:db8:ffff::12
PE13    2001:db8:ffff::13
PE14    2001:db8:ffff::14
EOS

{% if ROUTER_NUMBER in [11, 12, 13, 14] %}
# create vrf for CE router
ip link add CE type vrf table 1001
ip link set dev CE up
ip link set dev eth2 master CE
{% endif %}

exit 0
"""

# protocolsファイルの内容、BGPとISISだけ有効にします
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

FRR_CONF_TEMPLATE = """\
!
frr defaults traditional
hostname {{ HOSTNAME }}
log syslog informational
service integrated-vtysh-config
!
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
router bgp 65000
 bgp router-id 192.168.255.{{ ROUTER_NUMBER }}
 bgp log-neighbor-changes
 no bgp ebgp-requires-policy
 no bgp default ipv4-unicast
{% if ROUTER_NUMBER in [1, 2] %}
 bgp cluster-id 0.0.0.1
 neighbor P peer-group
 neighbor P remote-as internal
 neighbor PE peer-group
 neighbor PE remote-as internal
{% if ROUTER_NUMBER == 1 %}
 neighbor fd00:1:2:: peer-group P
{% endif %}
{% if ROUTER_NUMBER == 2 %}
 neighbor fd00:1:1:: peer-group P
{% endif %}
 neighbor fd00:1:11:: peer-group PE
 neighbor fd00:1:12:: peer-group PE
 neighbor fd00:1:13:: peer-group PE
 neighbor fd00:1:14:: peer-group PE
{% endif %}
{% if ROUTER_NUMBER in [11, 12, 13, 14] %}
 neighbor P peer-group
 neighbor P remote-as internal
 neighbor fd00:1:1:: peer-group P
 neighbor fd00:1:2:: peer-group P
{% endif %}
 !
 segment-routing srv6
  locator MAIN
  encap-behavior H_Encaps_Red
 exit
 !
 address-family ipv4 vpn
  {% if ROUTER_NUMBER in [1, 2] %}
  neighbor P activate
  neighbor PE activate
  neighbor PE route-reflector-client
  {% else %}
  neighbor P activate
  {% endif %}
  exit-address-family
 !
 address-family ipv6 vpn
  {% if ROUTER_NUMBER in [1, 2] %}
  neighbor P activate
  neighbor PE activate
  neighbor PE route-reflector-client
  {% else %}
  neighbor P activate
  {% endif %}
 exit-address-family
exit
{% if ROUTER_NUMBER in [11, 12, 13, 14] %}
!
router bgp 65000 vrf CE
 bgp router-id 192.168.255.{{ ROUTER_NUMBER }}
 bgp log-neighbor-changes
 no bgp ebgp-requires-policy
 no bgp default ipv4-unicast
 !
 address-family ipv4 unicast
  redistribute connected
  sid vpn export auto
  rd vpn export 65000:101
  rt vpn both 65000:101
  export vpn
  import vpn
  exit-address-family
exit
{% endif %}
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
{% if ROUTER_NUMBER == 1 %}
!
interface eth4
 description MANAGEMENT
 ip address 192.168.254.{{ ROUTER_NUMBER }}/24
 ip router isis 1
exit
{% endif %}
!
"""

CE_CONFIG_TEMPLATE = """\
hostname {{ HOSTNAME }}
!
ip route 0.0.0.0/0 {{ GW_ADDR }}
!
interface eth0
 ip address {{ PE_CE_ADDR }}
exit
!
"""

# Ubuntuノードに設定するcloud-initのJinja2テンプレート
UBUNTU_CONFIG_TEMPLATE = """\
#cloud-config
hostname: {{ UBUNTU_HOSTNAME }}
manage_etc_hosts: True
system_info:
  default_user:
    name: {{ UBUNTU_USERNAME }}
password: {{ UBUNTU_PASSWORD }}
chpasswd: { expire: False }
ssh_pwauth: True
ssh_authorized_keys:
  - ssh-rsa {{ SSH_PUBLIC_KEY }}

timezone: Asia/Tokyo

# locale: ja_JP.utf8
locale: en_US.UTF-8

# run apt update (default false)
# package_update: true

# run apt upgrade (default false)
# package_upgrade: true

# reboot if required
# package_reboot_if_required: true


write_files:
  #
  # refer to netplan document
  # https://netplan.readthedocs.io/en/latest/netplan-yaml/
  #
  - path: /etc/netplan/60-cloud-init.yaml
    permissions: '0600'
    owner: root:root
    content: |
      network:
        version: 2
        renderer: networkd
        ethernets:
          ens2:
            dhcp4: false
            dhcp6: false
            link-local: []
            addresses: [ 192.168.0.254/24 ]
          ens3:
            dhcp4: false
            dhcp6: false
            link-local: []
            addresses: [ 192.168.254.254/24 ]
            routes:
              - to: 0.0.0.0/0
                via: 192.168.254.1

runcmd:

  # add /etc/hosts
  - |
    cat - << 'EOS' >> /etc/hosts
    #
    {{ CML_ADDRESS }} cml
    192.168.255.1 P1
    192.168.255.2 P2
    192.168.255.11 PE1
    192.168.255.12 PE2
    192.168.255.13 PE3
    192.168.255.14 PE4
    EOS

  # Resize terminal window
  - |
    cat - << 'EOS' >> /etc/bash.bashrc
    rsz () if [[ -t 0 ]]; then local escape r c prompt=$(printf '\\e7\\e[r\\e[999;999H\\e[6n\\e8'); IFS='[;' read -sd R -p "$prompt" escape r c; stty cols $c rows $r; fi
    rsz
    EOS

  # Disable SSH client warnings
  - |
    cat << 'EOS' > /etc/ssh/ssh_config.d/99_lab_env.conf
    KexAlgorithms +diffie-hellman-group14-sha1,diffie-hellman-group1-sha1
    Ciphers +aes128-cbc,aes192-cbc,aes256-cbc,3des-cbc,aes128-ctr,aes192-ctr,aes256-ctr
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    EOS

  # Create SSH keys
  - ssh-keygen -t rsa -b 4096 -N "" -f /home/{{ UBUNTU_USERNAME }}/.ssh/id_rsa
  - chown -R {{ UBUNTU_USERNAME }}:{{ UBUNTU_USERNAME }} /home/{{ UBUNTU_USERNAME }}/.ssh
  - chmod 600 /home/{{ UBUNTU_USERNAME }}/.ssh/id_rsa*
  - chmod 700 /home/{{ UBUNTU_USERNAME }}/.ssh

  # Login as root for 192.168.255.*
  - |
    cat <<'EOS' >> /home/{{ UBUNTU_USERNAME }}/.ssh/config
    Host 192.168.255.*
      User root
    EOS
    chown {{ UBUNTU_USERNAME }}:{{ UBUNTU_USERNAME }} /home/{{ UBUNTU_USERNAME }}/.ssh/config
    chmod 600 /home/{{ UBUNTU_USERNAME }}/.ssh/config

  # Disable systemd-networkd-wait-online.service to speed up boot time
  - systemctl stop    systemd-networkd-wait-online.service
  - systemctl disable systemd-networkd-wait-online.service
  - systemctl mask    systemd-networkd-wait-online.service
  - netplan apply

  # Disable AppArmor
  - systemctl stop apparmor.service
  - systemctl disable apparmor.service

"""

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
    from jinja2 import Template
    from virl2_client import ClientLibrary
    from virl2_client.models.lab import Lab
except ImportError as e:
    logging.critical(str(e))
    sys.exit(-1)

#
# CMLに接続するための情報を取得する
#

# 環境変数が設定されている場合はそれを使用し、設定されていない場合はローカルファイルから読み込む
CML_ADDRESS = os.getenv("VIRL2_URL") or os.getenv("VIRL2_HOST")
CML_USERNAME = os.getenv("VIRL2_USER") or os.getenv("VIRL_USERNAME")
CML_PASSWORD = os.getenv("VIRL2_PASS") or os.getenv("VIRL_PASSWORD")

if not all([CML_ADDRESS, CML_USERNAME, CML_PASSWORD]):
    # ローカルファイルから読み込み
    try:
        from cml_config import CML_ADDRESS, CML_USERNAME, CML_PASSWORD
    except ImportError as e:
        logging.critical("CML connection info not found")
        logging.critical("Please set environment variables or create cml_config.py")
        sys.exit(-1)


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


    def start_lab(lab: Lab) -> None:
        state = lab.state()  # STARTED / STOPPED / DEFINED_ON_CORE
        if state == 'STOPPED' or state == 'DEFINED_ON_CORE':
            logger.info(f"Starting lab '{LAB_NAME}'")
            lab.start(wait=True)
            logger.info(f"Lab '{LAB_NAME}' started")
        else:
            logger.info(f"Lab '{LAB_NAME}' is already running")


    def stop_lab(lab: Lab) -> None:
        state = lab.state()  # STARTED / STOPPED / DEFINED_ON_CORE
        if state == 'STARTED':
            logger.info(f"Stopping lab '{LAB_NAME}'")
            lab.stop(wait=True)
            logger.info(f"Lab '{LAB_NAME}' stopped")
        else:
            logger.info(f"Lab '{LAB_NAME}' is not running")


    def delete_lab(lab: Lab) -> None:
        logger.info(f"Deleting lab '{LAB_NAME}'")
        stop_lab(lab)
        lab.wipe()
        lab.remove()
        logger.info(f"Lab '{LAB_NAME}' deleted")


    def create_lab(client: ClientLibrary) -> None:

        # 指定されたimage_definitionが存在するか確認して、なければ終了する
        image_defs = client.definitions.image_definitions()
        image_def_ids = [img['id'] for img in image_defs]
        if IMAGE_DEFINITION not in image_def_ids:
            logger.error(f"Specified image definition '{IMAGE_DEFINITION}' not found in CML.")
            return

        # ラボを新規作成
        lab = client.create_lab(title=LAB_NAME)

        # (X, Y)座標
        x = 0
        y = 0
        x_grid_width = 200
        y_grid_width = 160

        # Jinja2のTemplateをインスタンス化する
        boot_template = Template(BOOT_SH_TEXT)
        config_template = Template(FRR_CONF_TEMPLATE)
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

            # インタフェースを4+1個作成する
            for _ in range(5):
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
            boot_text = boot_template.render(template_context)

            # FRRに設定するファイル一式
            frr_configurations = [
                {
                    'name': 'frr.conf',
                    'content': config_text
                },
                {
                    'name': 'protocols',
                    'content': PROTOCOLS_TEXT
                },
                {   'name': 'boot.sh',
                    'content': boot_text
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
                },
                {   'name': 'boot.sh',
                    'content': BOOT_SH_TEXT
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
                "GW_ADDR": "10.0.11.1",
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
                "GW_ADDR": "10.0.12.1",
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
                "GW_ADDR": "10.0.13.1",
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
                "GW_ADDR": "10.0.14.1",
                "PE_CE_ADDR": "10.0.14.104/24"
            })
        }]
        ce104_eth0 = ce104.get_interface_by_label("eth0")
        pe14_eth2 = pe14.get_interface_by_label("eth2")
        lab.create_link(ce104_eth0, pe14_eth2, wait=True)

        #
        # 外部接続用のブリッジを作成する
        #
        ext_conn_node = lab.create_node("bridge1", "external_connector", x_grid_width, -y_grid_width, wait=True)

        # デフォルトはNATとして動作するので、これを"bridge1"に変更する
        # bridge1は追加したブリッジで、インターネット接続はない
        # このLANに足を出せば、母艦のWindows11の他、別のラボの仮想マシンであっても通信できる
        ext_conn_node.configuration = "bridge1"

        # インタフェースを一つ作る
        ext_conn_port = ext_conn_node.create_interface(0, wait=True)

        #
        # 踏み台用のubuntuノードを作成する
        #
        ubuntu_node = lab.create_node("ubuntu", "ubuntu", 0, -y_grid_width, wait=True)
        ubuntu_node.image_definition = UBUNTU_IMAGE_DEFINITION
        # ubuntuノードに設定するcloud-initの内容を作成する
        ubuntu_user_data = Template(UBUNTU_CONFIG_TEMPLATE).render({
            "UBUNTU_HOSTNAME": UBUNTU_HOSTNAME,
            "UBUNTU_USERNAME": UBUNTU_USERNAME,
            "UBUNTU_PASSWORD": UBUNTU_PASSWORD,
            "SSH_PUBLIC_KEY": SSH_PUBLIC_KEY
        })
        ubuntu_node.configuration = [
            {
                'name': 'user-data',
                'content': ubuntu_user_data
            },
            {
                'name': 'network-config',
                'content': '#network-config'
            }
        ]

        # pattyのタグを設定
        ubuntu_node.add_tag(tag=f"serial:{SERIAL_PORT + 200}")

        # ens2, ens3を作成
        for i in range(2):
            ubuntu_node.create_interface(i, wait=True)

        # ubuntuノードのens2を外部接続用ブリッジに接続する
        ubuntu_ens2 = ubuntu_node.get_interface_by_label("ens2")

        # 接続する
        lab.create_link(ubuntu_ens2, ext_conn_port, wait=True)

        # ubuntuノードのens3をPE1のeth4に接続する
        ubuntu_ens3 = ubuntu_node.get_interface_by_label("ens3")
        pe1_eth4 = p_routers[0].get_interface_by_label("eth4")
        lab.create_link(ubuntu_ens3, pe1_eth4, wait=True)

        #
        # アノテーションを作成する
        #
        text_content = 'FRR SRv6 uSID'
        create_text_annotation(lab, text_content, {
            'text_size': 20,
            'x1': -400.0,
            'y1': -160.0,
            'z_index': 0
        })

        text_content = 'fd00:0001: {{ 00 router-number }}/48'
        create_text_annotation(lab, text_content, {
            'x1': -400.0,
            'y1': -120.0,
            'z_index': 1
        })

        text_content = '49.0001 . 0000.0000.00{{ router-number }} . 00'
        create_text_annotation(lab, text_content, {
            'x1': -400.0,
            'y1': -80.0,
            'z_index': 2
        })

        text_content = '192.168.254.254'
        create_text_annotation(lab, text_content, {
            'x1': 20.0,
            'y1': -120.0,
            'z_index': 3
        })

        text_content = '192.168.0.254'
        create_text_annotation(lab, text_content, {
            'x1': 20.0,
            'y1': -200.0,
            'z_index': 3
        })

        # 楕円形のアノテーションを作成する
        lab.create_annotation('ellipse', **{
            'border_color': '#808080FF',
            'border_style': '',
            'color': '#E2D6D6',
            'rotation': 0,
            'thickness': 2,
            'x1': 280.0,
            'y1': -200.0,
            'x2': 40.0,
            'y2': 40.0,
            'z_index': 3
        })

        # 直線のアノテーションを作成する
        lab.create_annotation('line', **{
            'border_color': '#808080FF',
            'border_style': '',
            'color': '#FFFFFFFF',
            'line_end': 'arrow',
            'line_start': None,
            'thickness': 1,
            'x1': 240.0,
            'y1': -200.0,
            'x2': 160.0,
            'y2': -200.0,
            'z_index': 4
        })

        text_content = 'JUMP HOST'
        create_text_annotation(lab, text_content, {
            'x1': -80.0,
            'y1': -200.0,
            'z_index': 5
        })

        text_content = 'Windows Hyper-V HOST'
        create_text_annotation(lab, text_content, {
            'x1': 200.0,
            'y1': -240.0,
            'z_index': 5
        })

        text_content = '10.0.11.0/24'
        create_text_annotation(lab, text_content, {
            'x1': -360.0,
            'y1': 40.0,
            'z_index': 6
        })

        text_content = '10.0.12.0/24'
        create_text_annotation(lab, text_content, {
            'x1': -360.0,
            'y1': 200.0,
            'z_index': 6
        })

        text_content = '10.0.13.0/24'
        create_text_annotation(lab, text_content, {
            'x1': 240.0,
            'y1': 40.0,
            'z_index': 6
        })

        text_content = '10.0.14.0/24'
        create_text_annotation(lab, text_content, {
            'x1': 240.0,
            'y1': 200.0,
            'z_index': 6
        })

        lab.create_annotation('rectangle', **{
            'border_color': '#80808000',
            'border_radius': 0,
            'border_style': '',
            'color': '#DBEAEC',
            'rotation': 0,
            'thickness': 1,
            'x1': -480.0,
            'y1': -40.0,
            'x2': 160.0,
            'y2': 80.0,
            'z_index': 7
        })

        lab.create_annotation('rectangle', **{
            'border_color': '#80808000',
            'border_radius': 0,
            'border_style': '',
            'color': '#DBEAEC',
            'rotation': 0,
            'thickness': 1,
            'x1': -480.0,
            'y1': 120.0,
            'x2': 160.0,
            'y2': 80.0,
            'z_index': 7
        })

        lab.create_annotation('rectangle', **{
            'border_color': '#80808000',
            'border_radius': 0,
            'border_style': '',
            'color': '#DBEAEC',
            'rotation': 0,
            'thickness': 1,
            'x1': 320.0,
            'y1': -40.0,
            'x2': 160.0,
            'y2': 80.0,
            'z_index': 7
        })

        lab.create_annotation('rectangle', **{
            'border_color': '#80808000',
            'border_radius': 0,
            'border_style': '',
            'color': '#DBEAEC',
            'rotation': 0,
            'thickness': 1,
            'x1': 320.0,
            'y1': 120.0,
            'x2': 160.0,
            'y2': 80.0,
            'z_index': 7
        })

        logger.info(f"Lab '{LAB_NAME}' created")

        # start the lab
        # lab.start()

        # print nodes and interfaces states:
        #for node in lab.nodes():
        #    print(node, node.state, node.cpu_usage)
        #    for interface in node.interfaces():
        #        print(interface, interface.readpackets, interface.writepackets)


    def main() -> None:

        # 引数処理
        parser = argparse.ArgumentParser(description=LAB_DESCRIPTION)
        parser.add_argument('-c', '--create', action='store_true', default=False, help='Create lab')
        parser.add_argument('-d', '--delete', action='store_true', default=False, help='Delete lab')
        parser.add_argument('-p', '--pause', action='store_true', default=False, help='Pause lab')
        parser.add_argument('-s', '--start', action='store_true', default=False, help='Start lab')
        args = parser.parse_args()

        # 引数が何も指定されていない場合はhelpを表示して終了
        if len(sys.argv) == 1:
            parser.print_help()
            return

        # CMLを操作するvirl2_clientをインスタンス化
        client = ClientLibrary(f"https://{CML_ADDRESS}/", CML_USERNAME, CML_PASSWORD, ssl_verify=False)

        # 接続を待機する
        client.is_system_ready(wait=True)

        # 既存のラボがあれば取得する
        labs = client.find_labs_by_title(LAB_NAME)
        lab = labs[0] if labs and len(labs) > 0 else None

        if args.start:
            start_lab(lab) if lab else logger.error(f"Lab '{LAB_NAME}' not found")
            return

        if args.pause:
            stop_lab(lab) if lab else logger.error(f"Lab '{LAB_NAME}' not found")
            return

        if args.delete:
            delete_lab(lab) if lab else logger.error(f"Lab '{LAB_NAME}' not found")
            return

        if args.create:
            # 既存のラボがあれば削除する
            if lab:
                logger.info(f"Lab '{LAB_NAME}' already exists")
                delete_lab(lab)
            create_lab(client)

    #
    # 実行
    #
    main()
