#!/usr/bin/env python

#
# 標準ライブラリのインポート
#
import logging
import sys

#
# 外部ライブラリのインポート
#
try:
    from virl2_client import ClientLibrary
except ImportError as e:
    logging.critical(str(e))
    sys.exit(-1)

#
# ローカルファイルからの読み込み
#
from cml_config import CML_ADDRESS, CML_USERNAME, CML_PASSWORD


client = ClientLibrary(f"https://{CML_ADDRESS}/", CML_USERNAME, CML_PASSWORD, ssl_verify=False)

# 接続を待機する
client.is_system_ready(wait=True)

lab = client.create_lab()

r1 = lab.create_node("r1", "iosv", 50, 100)
r1.configuration = "hostname router1"
r2 = lab.create_node("r2", "iosv", 50, 200)
r2.configuration = "hostname router2"

# create a link between r1 and r2
r1_i1 = r1.create_interface()
r2_i1 = r2.create_interface()
lab.create_link(r1_i1, r2_i1)

# alternatively, use this convenience function:
lab.connect_two_nodes(r1, r2)

# start the lab
lab.start()

# print nodes and interfaces states:
for node in lab.nodes():
    print(node, node.state, node.cpu_usage)
    for interface in node.interfaces():
        print(interface, interface.readpackets, interface.writepackets)

lab.stop()

lab.wipe()

lab.remove_node(r2)

lab.remove()