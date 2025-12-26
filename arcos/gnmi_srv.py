#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
gNMI (gRPC Network Management Interface) サーバ実装

主な機能:
- Capabilities: サポートするモデルとエンコーディングの情報を返す
- Get: 指定されたパスの現在値を取得
- Set: 指定されたパスに値を設定
- Subscribe: 指定されたパスの値を定期的にストリーム配信


事前準備:
    Pythonモジュールをインストール
    pip install grpcio grpcio-tools
    pip install psutil

    protoファイルをダウンロード
    https://github.com/openconfig/gnmi

    protoファイルからPythonコードを生成する（ただし、これだとimportパスがおかしいので注意）
    python -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. gnmi.proto

    gnmicをインストール
    curl -sL https://get-gnmic.openconfig.net | sudo bash


使用例:
    # サーバ起動
    python gnmi_srv.py

    # クライアントからのアクセス例 (gnmicコマンド)
    gnmic -a localhost:50051 --insecure capabilities
    gnmic -a localhost:50051 --insecure get --path /system/config/hostname
    gnmic -a localhost:50051 --insecure get --path /system/state/cpu-usage
    gnmic -a localhost:50051 --insecure get --path /system/config/hostname --path /system/state/os-version
    gnmic -a localhost:50051 --insecure set --update /system/config/hostname:::string:::new-python-router
    gnmic -a localhost:50051 --insecure subscribe --path /system/state/cpu-usage --sample-interval 1s
    gnmic -a localhost:50051 --insecure subscribe --path /interfaces/interface/state/counters/in-octets --sample-interval 1s

"""

import os
import time
from concurrent import futures
from typing import Optional, Dict, Any, Iterator
from dataclasses import dataclass

# 警告を抑制するために環境変数を設定
os.environ['GRPC_VERBOSITY'] = 'NONE'

import grpc
import psutil

# gNMIの生成されたコードをインポート
import gnmi_pb2
import gnmi_pb2_grpc


# ============================================================================
# 設定定数
# ============================================================================

@dataclass
class ServerConfig:
    """gNMIサーバの設定"""
    port: int = 50051
    max_workers: int = 10
    default_subscribe_interval: float = 5.0
    shutdown_grace_period: int = 5


@dataclass
class ModelInfo:
    """サポートするモデル情報"""
    name: str = "openconfig-interfaces"
    organization: str = "openconfig"
    version: str = "0.1.0"
    gnmi_version: str = "0.8.0"


# ============================================================================
# ユーティリティ関数
# ============================================================================

def path_to_string(path: gnmi_pb2.Path) -> str:
    """
    gNMI Pathオブジェクトを文字列パス表現に変換

    Args:
        path: gNMI Pathオブジェクト

    Returns:
        パス文字列 (例: '/system/config/hostname')
    """
    if not path.elem:
        return "/"
    return "/" + "/".join([e.name for e in path.elem])


# ============================================================================
# データハンドラ
# ============================================================================

class SystemDataHandler:
    """システム情報を取得するハンドラ"""

    @staticmethod
    def get_cpu_usage() -> int:
        """CPU使用率を取得 (%)"""
        return int(psutil.cpu_percent(interval=None))

    @staticmethod
    def get_memory_usage() -> int:
        """メモリ使用率を取得 (%)"""
        return int(psutil.virtual_memory().percent)

    @staticmethod
    def get_os_version() -> str:
        """OS バージョン情報を取得"""
        return "Ubuntu 22.04 (WSL2)"


class InterfaceDataHandler:
    """ネットワークインターフェース情報を取得するハンドラ"""

    def __init__(self):
        self._net_io_cache: Optional[Dict[str, Any]] = None
        self._cache_time: float = 0
        self._cache_ttl: float = 0.1  # キャッシュの有効期間(秒)

    def _get_net_io(self) -> Dict[str, Any]:
        """ネットワークI/O統計を取得 (キャッシュ付き)"""
        current_time = time.time()
        if (self._net_io_cache is None or
            current_time - self._cache_time > self._cache_ttl):
            self._net_io_cache = psutil.net_io_counters(pernic=True)
            self._cache_time = current_time
        return self._net_io_cache

    def get_interface_stats(self, interface_name: Optional[str] = None) -> Any:
        """
        指定インターフェースの統計情報を取得

        Args:
            interface_name: インターフェース名。Noneの場合は最初のインターフェース

        Returns:
            psutil.snicstats オブジェクト
        """
        net_io = self._get_net_io()
        if interface_name and interface_name in net_io:
            return net_io[interface_name]
        return net_io[list(net_io.keys())[0]]

    def get_in_octets(self, interface_name: Optional[str] = None) -> int:
        """受信バイト数を取得"""
        stats = self.get_interface_stats(interface_name)
        return stats.bytes_recv

    def get_out_octets(self, interface_name: Optional[str] = None) -> int:
        """送信バイト数を取得"""
        stats = self.get_interface_stats(interface_name)
        return stats.bytes_sent


class PathValueResolver:
    """パス文字列から対応する値を取得する"""

    def __init__(self):
        self.system_handler = SystemDataHandler()
        self.interface_handler = InterfaceDataHandler()

    def resolve(self, path_str: str) -> Any:
        """
        パス文字列に対応する値を取得

        Args:
            path_str: パス文字列 (例: '/system/state/cpu-usage')

        Returns:
            パスに対応する値
        """
        # システム情報
        if "cpu-usage" in path_str:
            return self.system_handler.get_cpu_usage()
        elif "memory-usage" in path_str:
            return self.system_handler.get_memory_usage()
        elif "os-version" in path_str:
            return self.system_handler.get_os_version()

        # インターフェース情報
        elif "in-octets" in path_str:
            return self.interface_handler.get_in_octets()
        elif "out-octets" in path_str:
            return self.interface_handler.get_out_octets()

        # 未知のパス
        return "unknown-path"

    def set_typed_value(self, typed_value: gnmi_pb2.TypedValue, value: Any) -> None:
        """
        値の型に応じてTypedValueに設定

        Args:
            typed_value: 設定先のTypedValueオブジェクト
            value: 設定する値
        """
        if isinstance(value, int):
            if value >= 0:
                typed_value.uint_val = value
            else:
                typed_value.int_val = value
        elif isinstance(value, str):
            typed_value.string_val = value
        else:
            typed_value.string_val = str(value)


# ============================================================================
# gNMI サービス実装
# ============================================================================

class GNMIServicer(gnmi_pb2_grpc.gNMIServicer):
    """gNMI サービスの実装"""

    def __init__(self, config: ServerConfig = ServerConfig()):
        self.config = config
        self.model_info = ModelInfo()
        self.resolver = PathValueResolver()

    def Capabilities(self, request: gnmi_pb2.CapabilityRequest,
                     context: grpc.ServicerContext) -> gnmi_pb2.CapabilityResponse:
        """
        サポートするモデルとエンコーディング情報を返す
        """
        print(f"[{context.peer()}] Capabilities Requested")

        response = gnmi_pb2.CapabilityResponse()
        response.supported_models.add(
            name=self.model_info.name,
            organization=self.model_info.organization,
            version=self.model_info.version
        )
        response.supported_encodings.append(gnmi_pb2.JSON)
        response.gNMI_version = self.model_info.gnmi_version

        return response

    def Get(self, request: gnmi_pb2.GetRequest,
            context: grpc.ServicerContext) -> gnmi_pb2.GetResponse:
        """
        指定されたパスの現在値を取得
        """
        print(f"[{context.peer()}] Get Request Received")

        response = gnmi_pb2.GetResponse()
        notification = response.notification.add()
        notification.timestamp = int(time.time() * 1e9)

        for path in request.path:
            path_str = path_to_string(path)
            print(f"  Path: {path_str}")

            update = notification.update.add()
            update.path.CopyFrom(path)

            # パスに対応する値を取得して設定
            value = self.resolver.resolve(path_str)
            self.resolver.set_typed_value(update.val, value)

        return response

    def Set(self, request: gnmi_pb2.SetRequest,
            context: grpc.ServicerContext) -> gnmi_pb2.SetResponse:
        """
        指定されたパスに値を設定
        """
        print(f"[{context.peer()}] Set Request Received")

        response = gnmi_pb2.SetResponse()
        response.timestamp = int(time.time() * 1e9)

        for update in request.update:
            path_str = path_to_string(update.path)
            val = (update.val.string_val if update.val.HasField("string_val")
                   else update.val.int_val)
            print(f"  Update: {path_str} -> {val}")

            res = response.response.add()
            res.path.CopyFrom(update.path)
            res.op = gnmi_pb2.UpdateResult.UPDATE

        return response

    def Subscribe(self, request_iterator: Iterator[gnmi_pb2.SubscribeRequest],
                  context: grpc.ServicerContext) -> Iterator[gnmi_pb2.SubscribeResponse]:
        """
        指定されたパスの値を定期的にストリーム配信
        """
        print(f"[{context.peer()}] Subscribe Stream Started")

        try:
            req = next(request_iterator)
            if not req.HasField("subscribe"):
                return

            subscriptions = req.subscribe.subscription

            # サンプリング間隔を決定
            interval_sec = (subscriptions[0].sample_interval / 1e9
                          if subscriptions[0].sample_interval > 0
                          else self.config.default_subscribe_interval)

            print(f"  Interval: {interval_sec}s")

            while context.is_active():
                response = gnmi_pb2.SubscribeResponse()
                notification = response.update
                notification.timestamp = int(time.time() * 1e9)

                for sub in subscriptions:
                    path_str = path_to_string(sub.path)
                    update = notification.update.add()
                    update.path.CopyFrom(sub.path)

                    # パスに対応する値を取得して設定
                    value = self.resolver.resolve(path_str)
                    self.resolver.set_typed_value(update.val, value)

                yield response
                time.sleep(interval_sec)

        except Exception as e:
            print(f"  Error: {e}")


# ============================================================================
# サーバ起動
# ============================================================================

def serve(config: ServerConfig = ServerConfig()) -> None:
    """
    gNMIサーバを起動

    Args:
        config: サーバ設定
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=config.max_workers))
    gnmi_pb2_grpc.add_gNMIServicer_to_server(GNMIServicer(config), server)

    server.add_insecure_port(f'[::]:{config.port}')
    print(f"gNMI Server is running on port {config.port}...")
    print("Press Ctrl+C to stop the server safely.")

    server.start()

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\n[Shutdown] Stopping server...")
        server.stop(config.shutdown_grace_period)
        print("[Shutdown] Server stopped gracefully.")


if __name__ == '__main__':
    serve()