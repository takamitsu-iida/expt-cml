#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
protoファイルをダウンロード
https://github.com/openconfig/gnmi


pip install grpcio grpcio-tools
pip install psutil


protoファイルからPythonコードを生成、ただし、これだとimportパスがおかしいので注意
python -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. gnmi.proto


gnmicをインストール
curl -sL https://get-gnmic.openconfig.net | sudo bash

# ケーパビリティを取得
gnmic -a localhost:50051 --insecure capabilities

# パスを1つ取得
gnmic -a localhost:50051 --insecure get --path /system/config/hostname

# 2つのパスを同時に取得
gnmic -a localhost:50051 --insecure get \
  --path /system/config/hostname \
  --path /system/state/os-version

# subscribeでCPU使用率を5秒おきに取得
gnmic -a localhost:50051 --insecure subscribe --path /system/state/cpu-usage

# Setリクエストでホスト名を変更
gnmic -a localhost:50051 --insecure set --update /system/config/hostname:::string:::new-python-router

# subscribeでCPU使用率を1秒おきに取得
gnmic -a localhost:50051 --insecure subscribe --path /system/state/cpu-usage --sample-interval 1s

# psutilを使って実際の値を返すように修正した後のコマンド例
gnmic -a localhost:50051 --insecure get --path /system/state/memory-usage
gnmic -a localhost:50051 --insecure subscribe --path /system/state/cpu-usage --sample-interval 1s


# in-octets (受信バイト数) を1秒おきに監視
gnmic -a localhost:50051 --insecure subscribe --path /interfaces/interface/state/counters/in-octets --sample-interval 1s
"""

import os
import time
from concurrent import futures

# 警告を抑制するために環境変数を設定
# grpcをインポートする前に設定する必要がある
os.environ['GRPC_VERBOSITY'] = 'NONE'

import grpc
import psutil

# gNMIの生成されたコードをインポート
import gnmi_pb2
import gnmi_pb2_grpc


def path_to_string(path):
    """gNMI Pathオブジェクトを文字列 '/system/config/hostname' に変換する"""
    if not path.elem:
        return "/"
    return "/" + "/".join([e.name for e in path.elem])


class GNMIServicer(gnmi_pb2_grpc.gNMIServicer):
    def Capabilities(self, request, context):
        print(f"[{context.peer()}] Capabilities Requested")
        response = gnmi_pb2.CapabilityResponse()
        response.supported_models.add(name="openconfig-interfaces", organization="openconfig", version="0.1.0")
        response.supported_encodings.append(gnmi_pb2.JSON)
        response.gNMI_version = "0.8.0"
        return response

    def _Dummy_Get(self, request, context):
        print(f"[{context.peer()}] Get Request Received")
        response = gnmi_pb2.GetResponse()
        notification = response.notification.add()
        notification.timestamp = int(time.time() * 1e9)

        database = {
            "/system/config/hostname": ("string", "my-python-router"),
            "/system/state/os-version": ("string", "1.0.0-beta"),
            "/system/state/cpu-usage": ("int", 15)
        }

        for p in request.path:
            path_str = path_to_string(p)
            print(f"  Query: {path_str}")
            if path_str in database:
                v_type, v_value = database[path_str]
                update = notification.update.add()
                update.path.CopyFrom(p)
                if v_type == "string":
                    update.val.string_val = v_value
                elif v_type == "int":
                    update.val.int_val = v_value
        return response


    def Get(self, request, context):
        print(f"[{context.peer()}] Get Request Received")
        response = gnmi_pb2.GetResponse()
        notification = response.notification.add()
        notification.timestamp = int(time.time() * 1e9)

        for p in request.path:
            path_str = path_to_string(p)
            update = notification.update.add()
            update.path.CopyFrom(p)

            # --- 本物のデータを取得するロジック ---
            if "cpu-usage" in path_str:
                # interval=None だと直近の値を即座に返す
                update.val.int_val = int(psutil.cpu_percent(interval=None))
            elif "memory-usage" in path_str:
                # メモリ使用率（パーセント）
                update.val.int_val = int(psutil.virtual_memory().percent)
            elif "os-version" in path_str:
                update.val.string_val = "Ubuntu 22.04 (WSL2)" # 固定値でもOK
            else:
                update.val.string_val = "unknown-path"
            # ------------------------------------

            # --- ネットワーク統計の取得 ---
            # 例: /interfaces/interface[name=eth0]/state/counters/in-octets
            if "interfaces" in path_str:
                # すべてのインターフェース統計を取得
                net_io = psutil.net_io_counters(pernic=True)

                # 簡易的に、最初の物理インターフェースか 'eth0' を探す
                # 環境に合わせて 'Wi-Fi' や 'en0' などに変更してください
                iface_name = "eth0" if "eth0" in net_io else list(net_io.keys())[0]
                stats = net_io[iface_name]

                if "in-octets" in path_str:
                    update.val.int_val = stats.bytes_recv
                elif "out-octets" in path_str:
                    update.val.int_val = stats.bytes_sent
                print(f"  {iface_name} stats sent")
            # ----------------------------


        return response


    def Set(self, request, context):
        print(f"[{context.peer()}] Set Request Received")
        response = gnmi_pb2.SetResponse()
        response.timestamp = int(time.time() * 1e9)

        for update in request.update:
            path_str = path_to_string(update.path)
            val = update.val.string_val if update.val.HasField("string_val") else update.val.int_val
            print(f"  Update: {path_str} -> {val}")

            res = response.response.add()
            res.path.CopyFrom(update.path)
            res.op = gnmi_pb2.UpdateResult.UPDATE
        return response

    def _Dummy_Subscribe(self, request_iterator, context):

        import random

        print(f"[{context.peer()}] Subscribe Stream Started")
        try:
            # 1. クライアントからの最初のSubscription設定を取得
            req = next(request_iterator)
            if not req.HasField("subscribe"):
                return

            subs = req.subscribe.subscription

            # 代表して最初のパスの指定間隔を取得する（簡易実装）
            # sample_interval は nanoseconds (uint64)
            first_sub = subs[0]
            if first_sub.sample_interval > 0:
                # ナノ秒を秒に変換
                interval_sec = first_sub.sample_interval / 1e9
            else:
                # 指定がない場合はデフォルト5秒
                interval_sec = 5.0

            print(f"  Client requested interval: {interval_sec}s")

            # 2. 指定された間隔でループ
            while context.is_active():
                response = gnmi_pb2.SubscribeResponse()
                n = response.update
                n.timestamp = int(time.time() * 1e9)

                for sub in subs:
                    path_str = path_to_string(sub.path)
                    update = n.update.add()
                    update.path.CopyFrom(sub.path)

                    if "cpu-usage" in path_str:
                        update.val.int_val = random.randint(10, 80)
                    else:
                        update.val.string_val = f"interval-{interval_sec}s"

                yield response

                # クライアント指定の時間だけ待機
                time.sleep(interval_sec)

        except StopIteration:
            pass
        except Exception as e:
            print(f"  Subscribe Error: {e}")
        finally:
            print(f"[{context.peer()}] Subscribe Stream Closed")


    def Subscribe(self, request_iterator, context):
        print(f"[{context.peer()}] Subscribe Stream Started")
        try:
            req = next(request_iterator)
            if not req.HasField("subscribe"): return
            subs = req.subscribe.subscription

            # クライアント指定の間隔
            interval_sec = subs[0].sample_interval / 1e9 if subs[0].sample_interval > 0 else 5.0

            while context.is_active():
                response = gnmi_pb2.SubscribeResponse()
                n = response.update
                n.timestamp = int(time.time() * 1e9)

                net_io = psutil.net_io_counters(pernic=True)
                # 存在するインターフェース名を取得
                iface_name = "eth0" if "eth0" in net_io else list(net_io.keys())[0]
                stats = net_io[iface_name]

                for sub in subs:
                    path_str = path_to_string(sub.path)
                    update = n.update.add()
                    update.path.CopyFrom(sub.path)

                    # リアルタイムデータの生成
                    if "cpu-usage" in path_str:
                        update.val.int_val = int(psutil.cpu_percent(interval=None))
                    elif "memory-usage" in path_str:
                        update.val.int_val = int(psutil.virtual_memory().percent)
                    elif "in-octets" in path_str:
                        update.val.int_val = stats.bytes_recv
                    elif "out-octets" in path_str:
                        update.val.int_val = stats.bytes_sent
                    else:
                        update.val.string_val = "active"



                yield response
                time.sleep(interval_sec)
        except Exception as e:
            print(f"  Error: {e}")


def serve():

    # 同時接続数は最大で10に設定
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    gnmi_pb2_grpc.add_gNMIServicer_to_server(GNMIServicer(), server)

    # ポートのバインド
    port = 50051
    server.add_insecure_port(f'[::]:{port}')
    print(f"gNMI Server is running on port {port}...")
    print("Press Ctrl+C to stop the server safely.")

    server.start()

    try:
        # 終了シグナルを待機
        server.wait_for_termination()
    except KeyboardInterrupt:
        # Ctrl+C を検知した際の処理
        print("\n[Shutdown] Stopping server...")
        # 5秒間の猶予を持って停止。実行中のRPCをクローズする
        server.stop(5)
        print("[Shutdown] Server stopped gracefully.")

if __name__ == '__main__':
    serve()