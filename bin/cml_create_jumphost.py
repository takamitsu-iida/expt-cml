#!/usr/bin/env python

#
# 踏み台として動作するUbuntuノードを一つ作成します。
#

# Ubuntuは3本足で構成します。
#  - ens2: 外部接続用（NATに接続）
#  - ens3: Bridge1接続（Windowsホストとの接続用）
#  - ens4: ラボ内部の機器に接続する用

# スクリプトを引数無しで実行したときのヘルプに使うデスクリプション
SCRIPT_DESCRIPTION = 'create jump host lab'

# ラボの名前、既存で同じタイトルのラボがあれば削除してから作成する
LAB_TITLE = "jump_host_lab"

# ラボのデスクリプション
LAB_DESCRIPTION = "Jump host lab created by cml_create_jumphost.py"

# 管理LANのスイッチのラベル
MA_SWITCH_LABEL = "ma-switch"

# ノード定義
NODE_DEFINITION = "ubuntu"

# イメージ定義
# これはCMLのバージョンによって異なるので注意
# 2025年12月 CML2.9 でのUbuntu 24.04のイメージ定義
# このイメージ定義が存在しない場合はデフォルトのイメージを使用する
IMAGE_DEFINITION = "ubuntu-24-04-20250503"

# Ubuntuノードにつけるタグ
UBUNTU_TAG = "serial:6000"

# Ubuntuノードに与える初期設定のテンプレートのコンテキストで使うホスト名
UBUNTU_HOSTNAME = "jumphost"

# Ubuntuノードに与える初期設定のテンプレートのコンテキストで使うユーザ名
UBUNTU_USERNAME = "cisco"

# Ubuntuノードに与える初期設定のテンプレートのコンテキストで使うパスワード
UBUNTU_PASSWORD = "cisco"

# UbuntuのIPアドレス
UBUNTU_ENS3 = "192.168.0.100/24"
UBUNTU_ENS4 = "192.168.254.100/24"

# id_rsa.pubの中身をそのまま貼り付けます
# SSH_PUBLIC_KEY = "YOUR_SSH_PUBLIC_KEY_HERE"
SSH_PUBLIC_KEY = "AAAAB3NzaC1yc2EAAAADAQABAAABgQDdnRSDloG0LXnwXEoiy5YU39Sm6xTfvcpNm7az6An3rCfn2QC2unIWyN6sFWbKurGoZtA6QdKc8iSPvYPMjrS6P6iBW/cUJcoU8Y8BwUCnK33iKdCfkDWVDdNGN7joQ6DejhKTICTmcBJmwN9utJQVcagCO66Y76Xauub5WHs9BdAvpr+FCQh0eEQ7WZF1BQvH+bPXGmRxPQ8ViHvlUdgsVEq6kv9e/plh0ziXmkBXAw0bdquWu1pArX76jugQ4LXEJKgmQW/eBNiDgHv540nIH5nPkJ7OYwr8AbRCPX52vWhOr500U4U9n2FIVtMKkyVLHdLkx5kZ+cRJgOdOfMp8vaiEGI6Afl/q7+6n17SpXpXjo4G/NOE/xnjZ787jDwOkATiUGfCqLFaITaGsVcUL0vK2Nxb/tV5a2Rh1ELULIzPP0Sw5X2haIBLUKmQ/lmgbUDG6fqmb1z8XTon1DJQSLQXiojinknBKcMH4JepCrsYTAkpOsF6Y98sZKNIkAqU= iida@FCCLS0008993-00"

# Ubuntuノードに設定するcloud-initのJinja2テンプレート
UBUNTU_CONFIG_J2 = """#cloud-config
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

# run apt-get update
# default false
package_update: true

# default false
package_upgrade: true

# reboot if required
package_reboot_if_required: true

# packages
packages:
  - jq
  - yq
  - libxml2-utils  # xmllint
  - curl
  - wget
  - git
  - zip
  - unzip
  - make
  - python3-venv
  - direnv

  # TFTP client
  - tftp-hpa

  # DHCP/DNS/TFTP server
  - dnsmasq

  # SNMP
  - snmp
  - snmp-mibs-downloader

  # Radius
  - freeradius
  - freeradius-utils

  # NTP client/server
  - chrony

  # for apt-secure
  - gpg

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
            dhcp4: true
            dhcp6: false
            link-local: []
          ens3:
            dhcp4: false
            dhcp6: false
            addresses: [ {{ UBUNTU_ENS3 }} ]
          ens4:
            dhcp4: false
            dhcp6: false
            addresses: [ {{ UBUNTU_ENS4 }} ]

runcmd:

  # Add /etc/hosts
  - |
    cat - << 'EOS' >> /etc/hosts
    #
    {{ CML_ADDRESS }} cml

    #
    {% for rid in [1, 2] %}
    192.168.254.{{ rid }} P{{ rid }}
    2001:db8:ffff::{{ rid}} P{{ rid }}v6
    {% endfor %}

    {% for rid in [11, 12, 13, 14, 15, 16, 17, 18] %}
    192.168.254.{{ rid }} PE{{ rid }}
    2001:db8:ffff::{{ rid }} PE{{ rid }}v6
    {% endfor %}
    EOS

  # Resize terminal window
  - |
    cat - << 'EOS' >> /etc/bash.bashrc
    #
    rsz () if [[ -t 0 ]]; then local escape r c prompt=$(printf '\\e7\\e[r\\e[999;999H\\e[6n\\e8'); IFS='[;' read -sd R -p "$prompt" escape r c; stty cols $c rows $r; fi
    rsz
    EOS

  # TERM
  - |
    cat - << 'EOS' >> /etc/bash.bashrc
    #
    export TERM="linux"
    EOS

  # direnv
  - |
    cat - << 'EOS' >> /etc/bash.bashrc
    # direnv
    eval "$(direnv hook bash)"
    export EDITOR=vi
    EOS

  # Disable SSH client warnings
  - |
    cat - << 'EOS' > /etc/ssh/ssh_config.d/99_lab_env.conf
    KexAlgorithms +diffie-hellman-group14-sha1,diffie-hellman-group1-sha1
    Ciphers +aes128-cbc,aes192-cbc,aes256-cbc,3des-cbc,aes128-ctr,aes192-ctr,aes256-ctr
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
    EOS

  # Create SSH keys
  - sudo -u {{ UBUNTU_USERNAME}} ssh-keygen -t rsa -b 4096 -N "" -f /home/{{ UBUNTU_USERNAME }}/.ssh/id_rsa
  - chmod 600 /home/{{ UBUNTU_USERNAME }}/.ssh/id_rsa*
  - chmod 700 /home/{{ UBUNTU_USERNAME }}/.ssh

  # Disable systemd-networkd-wait-online.service to speed up boot time
  - systemctl stop     systemd-networkd-wait-online.service
  - systemctl disable systemd-networkd-wait-online.service
  - systemctl mask    systemd-networkd-wait-online.service
  - netplan apply

  # Disable AppArmor
  - systemctl stop apparmor.service
  - systemctl disable apparmor.service
  - systemctl mask apparmor.service

  # Disable systemd-resolved
  - systemctl stop systemd-resolved
  - systemctl disable systemd-resolved

  # create /etc/dnsmasq.conf
  - |
    cat - << 'EOS' > /etc/dnsmasq.conf
    # ens4 インターフェースのみでリッスンする
    interface=ens4

    # 指定したインターフェース/IPアドレスにのみバインドする
    bind-interfaces

    # ドメイン名の設定 (option domain-name)
    domain=iida.local

    # DHCPリース範囲の設定 (subnet と range)
    # 形式: dhcp-range=<開始IP>,<終了IP>,<リース時間>
    # デフォルトリース時間 600秒 (10分)、最大リース時間 7200秒 (2時間)
    dhcp-range=192.168.254.101,192.168.254.199,7200s

    # ログの出力先
    log-facility=/var/log/dnsmasq.log

    # DHCPオプション
    # 自分自身を参照させる
    dhcp-option=option:dns-server,192.168.254.100

    # /etc/dnsmasq.d 内の .conf ファイルをすべて読み込む
    conf-dir=/etc/dnsmasq.d

    # DNS設定
    server=8.8.8.8
    server=8.8.4.4

    # ホスト名だけのクエリは外部に転送しない
    domain-needed

    # ローカルネットワーク内の逆引きは外部に転送しない
    bogus-priv

    # dnsmasq自身は/etc/resolv.confを参照しない
    no-resolv

    # TFTP サーバを有効にする
    enable-tftp

    # TFTP のルートディレクトリを指定
    tftp-root=/srv/tftp
    EOS

  # create /etc/dnsmasq.d/host.conf
  # Vendor-specific 0x43, Code 35=0x0023
  # 43,00:23 + 00:1d (URL文字列の長さ 29=0x1d) + URL文字列の16進
  - |
    cat - << 'EOS' > /etc/dnsmasq.d/host.conf

    {% for rid in [1, 2] %}
        {%- set url = "tftp://192.168.254.100/P" ~ rid ~ ".cfg" -%}
        {%- set url_len = url | length -%}
    dhcp-host=52:54:00:00:00:{{ '%02d' % rid }},192.168.254.{{ rid }},set:P{{ rid }}
    dhcp-option-force=tag:P{{ rid }},43,00:23:00:{{ '%02x' % url_len }}:{% for char in url -%}{{ "%02x" % char.encode('ascii')[0] }}{{ ":" if not loop.last }}{% endfor %}
    {% endfor %}

    {% for rid in [11, 12, 13, 14, 15, 16, 17, 18] %}
        {%- set url = "tftp://192.168.254.100/PE" ~ rid ~ ".cfg" -%}
        {%- set url_len = url | length -%}
    dhcp-host=52:54:00:00:00:{{ '%02d' % rid }},192.168.254.{{ rid }},set:PE{{ rid }}
    dhcp-option-force=tag:PE{{ rid }},43,00:23:00:{{ '%02x' % url_len }}:{% for char in url -%}{{ "%02x" % char.encode('ascii')[0] }}{{ ":" if not loop.last }}{% endfor %}
    {% endfor %}
    EOS

  # chnage ownership of /srv/tftp
  - mkdir -p /srv/tftp
  - chown nobody:nogroup /srv/tftp
  - chmod 777 /srv/tftp

  # 自分自身のdnsmasqを参照
  - rm -f /etc/resolv.conf
  - sh -c 'echo "nameserver 127.0.0.1" > /etc/resolv.conf'
  - sh -c 'echo "nameserver 8.8.8.8" >> /etc/resolv.conf'

  # restart dnsmasq
  - systemctl restart dnsmasq

  # freeradius clients.conf
  - |
    cat - << 'EOS' >> /etc/freeradius/3.0/clients.conf
    client ma-lan {
        ipaddr = 192.168.254.0/24
        secret = cisco123
    }
    EOS

  - |
    cat - << 'EOS' >> /etc/freeradius/3.0/users
    test Cleartext-Password := "test"
        Reply-Message = "Hello, test user!"

    operator Cleartext-Password := "operator"
        Service-Type = Login,
        Login-Service = Telnet,SSH,
        Login-Host = %{NAS-IP-Address}
    EOS

  # restart freeradius
  - systemctl restart freeradius

  # fix chrony config
  - sed -i 's/^pool /# pool /g' /etc/chrony/chrony.conf
  - echo "local stratum 10" >> /etc/chrony/chrony.conf
  - echo "server ntp.nict.jp iburst" >> /etc/chrony/chrony.conf
  - echo "server ntp.jst.mfeed.ad.jp iburst" >> /etc/chrony/chrony.conf
  - echo "allow 192.168.254.0/24" >> /etc/chrony/chrony.conf

  # restart chrony
  - systemctl restart chrony

  # /etc/snmp/snmp.confの mibs 設定を変更
  - sed -i.bak 's/^mibs :/# mibs :/' /etc/snmp/snmp.conf

  #
  # Telegraf インストール
  #

  # GPGキーの追加
  - wget -qO- https://repos.influxdata.com/influxdb.key | gpg --dearmor | tee /etc/apt/trusted.gpg.d/influxdb.gpg > /dev/null

  # APTリポジトリの追加
  - |
    DISTRIB_ID=$(grep -E '^ID=' /etc/os-release | cut -d'=' -f2 | tr -d '"')
    DISTRIB_CODENAME=$(grep -E '^VERSION_CODENAME=' /etc/os-release | cut -d'=' -f2 | tr -d '"')
    echo "deb [signed-by=/etc/apt/trusted.gpg.d/influxdb.gpg] https://repos.influxdata.com/${DISTRIB_ID,,} ${DISTRIB_CODENAME} stable" | tee /etc/apt/sources.list.d/influxdata.list > /dev/null

  # Telegrafのインストール
  - apt update
  - apt install -y telegraf

  # Telegrafを自動起動しないようにする
  - systemctl stop telegraf    # サービスが自動的に起動していれば停止
  - systemctl disable telegraf # システム起動時に自動的に開始されないように無効化

""".strip()


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
    from virl2_client.models.lab import Lab, Node
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

    # ラボを新規作成
    lab = client.create_lab(title=title, description=description)

    # 外部接続用のNATを作る
    ext_conn_node = lab.create_node(label="ext-conn-0", node_definition="external_connector", x=0, y=-240)

    # bridge1を作る
    bridge1_node = lab.create_node(label="bridge1", node_definition="external_connector", x=160, y=-120)
    bridge1_node.configuration = [
        {
            'name': 'default',
            'content': 'bridge1'
        }
    ]

    # ma switchを作る
    ma_switch_node = lab.create_node(label=MA_SWITCH_LABEL, node_definition="unmanaged_switch", x=0, y=0)

    # リンクを非表示にする
    ma_switch_node.hide_links = True

    # インタフェースを作成する
    for i in range(16):
        ma_switch_node.create_interface(i, wait=True)

    #
    # アノテーション
    #

    # 楕円形のアノテーションを作成する(Hyper-V hostを囲む)
    lab.create_annotation('ellipse', **{
        'border_color': '#808080FF',
        'border_style': '',
        'color': '#E2D6D6',
        'rotation': 0,
        'thickness': 2,
        'x1': 360.0,
        'y1': -120.0,
        'x2': 40.0,
        'y2': 40.0,
        'z_index': 0
    })

    # 直線のアノテーションを作成する
    lab.create_annotation('line', **{
        'border_color': '#808080FF',
        'border_style': '',
        'color': '#FFFFFFFF',
        'line_end': None,
        'line_start': None,
        'thickness': 1,
        'x1': 180.0,
        'y1': -120.0,
        'x2': 320.0,
        'y2': -120.0,
        'z_index': 0
    })

    # テキストのアノテーションを作成する
    create_text_annotation(lab, "192.168.0.0/24", {'x1': 120.0, 'y1': -160.0, 'z_index': 1})
    create_text_annotation(lab, "192.168.254.0/24", {'x1': -160.0, 'y1': 0.0, 'z_index': 1})
    create_text_annotation(lab, ".100", {'text_size': 16, 'text_bold': True, 'x1': 40.0, 'y1': -80.0, 'z_index': 1})
    create_text_annotation(lab, "Hyper-V host\n192.168.0.198/24", {'x1': 320.0, 'y1': -160.0, 'z_index': 1})

    # ubuntuのインスタンスを作る
    ubuntu_node = lab.create_node(label=UBUNTU_HOSTNAME, node_definition="ubuntu", x=0, y=-120)

    # 起動イメージを指定する
    if is_exist_image_definition(client, IMAGE_DEFINITION):
        ubuntu_node.image_definition = IMAGE_DEFINITION
    else:
        logger.warning(f"Image definition '{IMAGE_DEFINITION}' not found. Using default image for node definition '{NODE_DEFINITION}'")

    # 初期状態はインタフェースが存在しないので追加、3本足にする
    #
    #  external nat
    #     |
    #    (ens2)
    #     |
    #    Ubuntu-(ens3)----bridge1 (to Windows Hyper-V host)
    #     |
    #    (ens4)
    #     |
    #   ma-switch (to lab devices)
    #
    for i in range(3):
        ubuntu_node.create_interface(i, wait=True)

    # ubuntuとNATを接続する
    lab.connect_two_nodes(ubuntu_node, ext_conn_node)

    # ubuntuとbridge1を接続する
    lab.connect_two_nodes(ubuntu_node, bridge1_node)

    # ubuntuとma switchを接続する
    lab.connect_two_nodes(ubuntu_node, ma_switch_node)

    # Ubuntuのcloud-initテンプレートを取得する
    ubuntu_template = Template(UBUNTU_CONFIG_J2)

    # テンプレートに渡すコンテキストオブジェクト
    context = {
        "CML_ADDRESS": CML_ADDRESS,
        "UBUNTU_HOSTNAME": UBUNTU_HOSTNAME,
        "UBUNTU_USERNAME": UBUNTU_USERNAME,
        "UBUNTU_PASSWORD": UBUNTU_PASSWORD,
        "UBUNTU_ENS3": UBUNTU_ENS3,
        "UBUNTU_ENS4": UBUNTU_ENS4,
        "SSH_PUBLIC_KEY": SSH_PUBLIC_KEY,
    }

    # Ubuntuに設定するcloud-init.yamlのテキストを作る
    config_text = ubuntu_template.render(context)

    # ノードのconfigにcloud-init.yamlのテキストを設定する
    ubuntu_node.configuration = [
        {
            'name': 'user-data',
            'content': config_text
        },
        {
            'name': 'network-config',
            'content': '#network-config'
        }
    ]

    # タグを設定する
    ubuntu_node.add_tag(tag=UBUNTU_TAG)

    logger.info(f"Lab '{title}' created successfully")
    logger.info(f"id: {lab.id}")


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
            # 既存のラボがあれば削除する
            if lab:
                logger.info(f"Lab '{args.title}' already exists")
                delete_lab(lab)
            create_lab(client, args.title, args.description)

    #
    # 実行
    ##
    main()
