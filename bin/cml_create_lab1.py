#!/usr/bin/env python


###########################################################

#
# 作成するラボの情報
#

# ラボの名前、既存で同じタイトルのラボがあれば削除してから作成する
LAB_NAME = "cml_create_lab1"

# ノード定義
NODE_DEFINITION = "ubuntu"

# イメージ定義
IMAGE_DEFINITION = "ubuntu-24-04-20250503"

# ノードにつけるタグ
NODE_TAG = "serial:6000"

# Ubuntuノードに与える初期設定のテンプレートのコンテキストで使うホスト名
UBUNTU_HOSTNAME = "ubuntu-0"

# Ubuntuノードに与える初期設定のテンプレートのコンテキストで使うユーザ名
UBUNTU_USERNAME = "cisco"

# Ubuntuノードに与える初期設定のテンプレートのコンテキストで使うパスワード
UBUNTU_PASSWORD = "cisco"

# id_rsa.pubの中身をそのまま貼り付けます
# SSH_PUBLIC_KEY = "YOUR_SSH_PUBLIC_KEY_HERE"
SSH_PUBLIC_KEY = "AAAAB3NzaC1yc2EAAAADAQABAAABgQDdnRSDloG0LXnwXEoiy5YU39Sm6xTfvcpNm7az6An3rCfn2QC2unIWyN6sFWbKurGoZtA6QdKc8iSPvYPMjrS6P6iBW/cUJcoU8Y8BwUCnK33iKdCfkDWVDdNGN7joQ6DejhKTICTmcBJmwN9utJQVcagCO66Y76Xauub5WHs9BdAvpr+FCQh0eEQ7WZF1BQvH+bPXGmRxPQ8ViHvlUdgsVEq6kv9e/plh0ziXmkBXAw0bdquWu1pArX76jugQ4LXEJKgmQW/eBNiDgHv540nIH5nPkJ7OYwr8AbRCPX52vWhOr500U4U9n2FIVtMKkyVLHdLkx5kZ+cRJgOdOfMp8vaiEGI6Afl/q7+6n17SpXpXjo4G/NOE/xnjZ787jDwOkATiUGfCqLFaITaGsVcUL0vK2Nxb/tV5a2Rh1ELULIzPP0Sw5X2haIBLUKmQ/lmgbUDG6fqmb1z8XTon1DJQSLQXiojinknBKcMH4JepCrsYTAkpOsF6Y98sZKNIkAqU= iida@FCCLS0008993-00"

# Ubuntuノードに設定するcloud-initのJinja2テンプレート
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

# run apt-get update
# default false
package_update: true

# default false
package_upgrade: true

# reboot if required
package_reboot_if_required: true

# packages
packages:
  - git
  - ansible

#
# ansible-pull
#

#ansible:
#  install_method: distro
#  package_name: ansible-core
#  pull:
#    url: "https://github.com/takamitsu-iida/expt-cml.git"
#    playbook_name: playbook.yaml

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

runcmd:

  - |
    cat - << 'EOS' >> /etc/bash.bashrc
    rsz () if [[ -t 0 ]]; then local escape r c prompt=$(printf '\e7\e[r\e[999;999H\e[6n\e8'); IFS='[;' read -sd R -p "$prompt" escape r c; stty cols $c rows $r; fi
    rsz
    EOS

  - systemctl disable systemd-networkd-wait-online.service
  - systemctl mask    systemd-networkd-wait-online.service
  - netplan apply
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
        parser = argparse.ArgumentParser(description='create lab')
        parser.add_argument('-d', '--delete', action='store_true', default=False, help='Delete lab')
        args = parser.parse_args()

        client = ClientLibrary(f"https://{CML_ADDRESS}/", CML_USERNAME, CML_PASSWORD, ssl_verify=False)

        # 接続を待機する
        client.is_system_ready(wait=True)

        # 同タイトルのラボを消す
        for lab in client.find_labs_by_title(LAB_NAME):
            lab.stop()
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

        # 外部接続用のNATを作る
        ext_conn_node = lab.create_node(label="ext-conn-0", node_definition="external_connector", x=0, y=0)

        # ubuntuのインスタンスを作る
        ubuntu_node = lab.create_node(label=UBUNTU_HOSTNAME, node_definition="ubuntu", x=0, y=200)

        # 起動イメージを指定する
        ubuntu_node.image_definition = IMAGE_DEFINITION

        # 初期状態はインタフェースが存在しないので、追加する
        # Ubuntuのslot番号の範囲は0-7
        # slot番号はインタフェース名ではない
        # ens2-ens9が作られる
        for i in range(8):
            ubuntu_node.create_interface(i, wait=True)

        # NATとubuntuを接続する
        lab.connect_two_nodes(ext_conn_node, ubuntu_node)

        # Jinja2のTemplateをインスタンス化する
        template = Template(UBUNTU_CONFIG)

        # templateに渡すコンテキストオブジェクト
        context = {
            "HOSTNAME": UBUNTU_HOSTNAME,
            "USERNAME": UBUNTU_USERNAME,
            "PASSWORD": UBUNTU_PASSWORD,
            "SSH_PUBLIC_KEY": SSH_PUBLIC_KEY
        }

        # Ubuntuに設定するcloud-init.yamlのテキストを作る
        config_text = template.render(context)

        # ノードのconfigにcloud-init.yamlのテキストを設定する
        ubuntu_node.configuration = config_text

        # タグを設定する
        # "serial:6000"
        ubuntu_node.add_tag(tag=NODE_TAG)

        # start the lab
        lab.start()

        return 0

    # 実行
    sys.exit(main())
