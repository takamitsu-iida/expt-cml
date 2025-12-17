#!/usr/bin/env python

r"""
【事前準備】

1. 適当な作業ディレクトリ(tmp)を作成して移動

mkdir -p tmp

tmpは.gitignoreで管理対象外に指定済み


2. tmpディレクトリに移動

cd tmp

3. 必要なディレクトリ構造を作成

mkdir -p github.com/openconfig/gnmi/proto/gnmi
mkdir -p github.com/openconfig/gnmi/proto/gnmi_ext

4. NMI protoファイルを取得

wget -O github.com/openconfig/gnmi/proto/gnmi/gnmi.proto \
    https://raw.githubusercontent.com/openconfig/gnmi/master/proto/gnmi/gnmi.proto

wget -O github.com/openconfig/gnmi/proto/gnmi_ext/gnmi_ext.proto \
    https://raw.githubusercontent.com/openconfig/gnmi/master/proto/gnmi_ext/gnmi_ext.proto


5. 必要なライブラリをインストール

pip install grpcio grpcio-tools

6. プロトコルバッファをコンパイル

python -m grpc_tools.protoc \
    -I. \
    --python_out=. \
    --pyi_out=. \
    --grpc_python_out=. \
    github.com/openconfig/gnmi/proto/gnmi/gnmi.proto \
    github.com/openconfig/gnmi/proto/gnmi_ext/gnmi_ext.proto

これで、gnmi_pb2.py と gnmi_pb2_grpc.py が生成されるので、この2つを使いたい場所にコピー

cp github/com/openconfig/gnmi/proto/gnmi/gnmi_pb2.py ..
cp github/com/openconfig/gnmi/proto/gnmi/gnmi_pb2_grpc.py ..
cp github/com/openconfig/gnmi/proto/gnmi_ext/gnmi_ext_pb2.py ..

7. tmpディレクトリを削除して元のディレクトリに戻る

cd ..
rm -rf tmp


8. コピーした gnmi_pb2.py と gnmi_pb2_grpc.py のインポートパスを手動で編集するか、sedコマンドで修正する

# gnmi_pb2.py のインポートパスを修正
sed -i 's/from github\.com\.openconfig\.gnmi\.proto\.gnmi_ext import gnmi_ext_pb2/import gnmi_ext_pb2/g' gnmi_pb2.py

# gnmi_pb2_grpc.py も同様に修正（生成されている場合）
sed -i 's/from github\.com\.openconfig\.gnmi\.proto\.gnmi import gnmi_pb2/import gnmi_pb2/g' gnmi_pb2_grpc.py
sed -i 's/from github\.com\.openconfig\.gnmi\.proto\.gnmi import gnmi_pb2 as gnmi__pb2/import gnmi_pb2 as gnmi__pb2/g' gnmi_pb2_grpc.py
sed -i 's/import gnmi_ext_pb2 as github_dot_com_dot_openconfig_dot_gnmi_dot_proto_dot_gnmi__ext_dot_gnmi__ext__pb2/import gnmi_ext_pb2/g' gnmi_pb2.py

cd ~/git/expt-cml/arcos

# 念のため確認
grep "import gnmi_ext_pb2" gnmi_pb2.py

"""

import asyncio
import logging
import random
import time
from typing import Dict, Any, Optional
from enum import Enum
from collections import defaultdict

import grpc.aio

import gnmi_pb2
import gnmi_pb2_grpc

# ============================================================================
# ロギング設定
# ============================================================================

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('gNMI_Telemetry')

# ============================================================================
# 定数定義
# ============================================================================

# 再接続戦略の設定
INITIAL_RECONNECT_DELAY_SEC = 1       # 最初の再接続待機時間（秒）
MAX_RECONNECT_DELAY_SEC = 120         # 最大再接続待機時間（秒）
RETRY_SUCCESS_RESET_TIME_SEC = 600    # この時間成功が続いたらリトライ数をリセット（秒）

# gRPC接続設定
GRPC_CONNECT_TIMEOUT_SEC = 10
GRPC_KEEPALIVE_TIME_SEC = 30
GRPC_KEEPALIVE_TIMEOUT_SEC = 5

# データ処理設定
DATA_QUEUE_MAX_SIZE = 500             # データキューの最大サイズ
DATA_BATCH_SIZE_FOR_WRITE = 10        # この数に達したらデータベースに書き込む
DATA_BUFFER_FETCH_LIMIT = 50          # 1回で取得する最大データ数
DATA_PROCESSOR_TIMEOUT_SEC = 1.0      # データ処理のタイムアウト（秒）

# gNMI購読設定
GNMI_SAMPLE_INTERVAL_NANOSEC = 30_000_000_000  # サンプル間隔（30秒、ナノ秒）

# テレメトリ収集パス
SAMPLE_PATHS = [
    # "/interfaces/interface[name=*]/state/counters/in-octets",
    # "/interfaces/interface[name=*]/state/counters/out-octets",
]

ON_CHANGE_PATHS = [
    "interfaces/interface[name=*]/state/oper-status"
]


# バックプレッシャー判定の際のジッター範囲
BACKOFF_JITTER_MIN = 0.8
BACKOFF_JITTER_MAX = 1.2


# ============================================================================
# 列挙型・クラス定義
# ============================================================================

class RetryableError(Enum):
    """リトライ可能なgRPCエラーの定義"""
    UNAVAILABLE = "unavailable"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    INTERNAL = "internal"
    UNKNOWN = "unknown"


class CollectorMetrics:
    """
    各ホストのテレメトリ収集状況を記録するメトリクス管理クラス。

    監視項目:
    - total_records: 収集したレコード数
    - errors: 発生したエラー数
    - last_error: 最後に発生したエラー内容
    - reconnects: 再接続回数
    - last_update_time: 最後にデータを受信した時刻
    - on_change_events: ON_CHANGE イベント数
    """

    def __init__(self):
        """メトリクスコンテナを初期化"""
        self.metrics = defaultdict(lambda: {
            'total_records': 0,
            'errors': 0,
            'last_error': None,
            'reconnects': 0,
            'last_update_time': None,
            'on_change_events': 0
        })
        # ON_CHANGE イベントの前の値を保持（変更検知用）
        self.previous_values = {}

    def record_data(self, host: str) -> None:
        """
        ホストからデータ受信を記録

        Args:
            host: ホストアドレス
        """
        self.metrics[host]['total_records'] += 1
        self.metrics[host]['last_update_time'] = time.time()

    def record_error(self, host: str, error: str) -> None:
        """
        ホストでのエラー発生を記録

        Args:
            host: ホストアドレス
            error: エラーメッセージまたはエラーコード
        """
        self.metrics[host]['errors'] += 1
        self.metrics[host]['last_error'] = error

    def record_reconnect(self, host: str) -> None:
        """
        ホストへの再接続を記録

        Args:
            host: ホストアドレス
        """
        self.metrics[host]['reconnects'] += 1

    def record_on_change_event(self, host: str) -> None:
        """
        ON_CHANGE イベント検知を記録

        Args:
            host: ホストアドレス
        """
        self.metrics[host]['on_change_events'] += 1

    def store_previous_value(self, key: str, value: str) -> None:
        """
        前の値を保存（変更検知用）

        Args:
            key: ホスト+パスの複合キー
            value: 値
        """
        self.previous_values[key] = value

    def get_previous_value(self, key: str) -> Optional[str]:
        """
        前の値を取得

        Args:
            key: ホスト+パスの複合キー

        Returns:
            前の値（ない場合は None）
        """
        return self.previous_values.get(key)

    def get_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        全ホストのメトリクスサマリを取得

        Returns:
            ホスト別のメトリクス辞書
        """
        return dict(self.metrics)


# ============================================================================
# ユーティリティ関数
# ============================================================================

def is_retryable_error(error: grpc.aio.AioRpcError) -> bool:
    """
    gRPCエラーがリトライ可能かを判定

    リトライ可能なエラー: UNAVAILABLE, RESOURCE_EXHAUSTED, INTERNAL, UNKNOWN
    リトライ不可能なエラー: UNAUTHENTICATED, PERMISSION_DENIED, NOT_FOUND など

    Args:
        error: gRPCエラーオブジェクト

    Returns:
        True: リトライすべき / False: リトライすべきでない
    """
    retryable_codes = {
        grpc.StatusCode.UNAVAILABLE,
        grpc.StatusCode.RESOURCE_EXHAUSTED,
        grpc.StatusCode.INTERNAL,
        grpc.StatusCode.UNKNOWN,
    }
    return error.code() in retryable_codes


def calculate_backoff_delay(
    retry_count: int,
    initial_delay: int = INITIAL_RECONNECT_DELAY_SEC,
    max_delay: int = MAX_RECONNECT_DELAY_SEC
) -> float:
    """
    指数バックオフ + ランダムジッターで再接続待機時間を計算

    式: min(initial_delay * 2^retry_count, max_delay) * random(0.8～1.2)

    例: retry_count=0 -> 1秒, retry_count=1 -> 2秒, retry_count=2 -> 4秒...

    Args:
        retry_count: 再試行回数（0から始まる）
        initial_delay: 初期待機時間（秒）
        max_delay: 最大待機時間（秒）

    Returns:
        計算された待機時間（秒、float）
    """
    exponential_delay = min(initial_delay * (2 ** retry_count), max_delay)
    jitter = random.uniform(BACKOFF_JITTER_MIN, BACKOFF_JITTER_MAX)
    return exponential_delay * jitter


def build_gnmi_subscription_request() -> gnmi_pb2.SubscribeRequest:
    """
    gNMI購読リクエストを構築

    SAMPLE モード（定期的なサンプリング）と ON_CHANGE モード（イベント検知）の両方のパスを含める

    Returns:
        構築されたSubscribeRequest
    """
    subscriptions = []

    # ========================================================
    # SAMPLE モード: 定期的なサンプリング
    # ========================================================
    for path_str in SAMPLE_PATHS:
        subscription = gnmi_pb2.Subscription(
            path=gnmi_pb2.Path(
                elem=[
                    gnmi_pb2.PathElem(name="interfaces"),
                    gnmi_pb2.PathElem(name="interface", key={"name": "*"}),
                    gnmi_pb2.PathElem(name="state"),
                    gnmi_pb2.PathElem(name="counters"),
                    gnmi_pb2.PathElem(name=path_str.split("/")[-1]),
                ]
            ),
            mode=gnmi_pb2.SubscriptionMode.SAMPLE,
            sample_interval=GNMI_SAMPLE_INTERVAL_NANOSEC,
        )
        subscriptions.append(subscription)

    # ========================================================
    # ON_CHANGE モード: 値変更を検知して通知
    # ========================================================
    for path_str in ON_CHANGE_PATHS:
        # パス文字列から " ON_CHANGE" 部分を除去
        clean_path = path_str.replace(" ON_CHANGE", "").strip()

        subscription = gnmi_pb2.Subscription(
            path=gnmi_pb2.Path(
                elem=[
                    gnmi_pb2.PathElem(name="interfaces"),
                    gnmi_pb2.PathElem(name="interface", key={"name": "*"}),
                    gnmi_pb2.PathElem(name="subinterfaces"),
                    gnmi_pb2.PathElem(name="subinterface"),
                    gnmi_pb2.PathElem(name="state"),
                    gnmi_pb2.PathElem(name="ifindex"),
                ]
            ),
            mode=gnmi_pb2.SubscriptionMode.ON_CHANGE,
        )
        subscriptions.append(subscription)

    return gnmi_pb2.SubscribeRequest(
        subscribe=gnmi_pb2.SubscriptionList(
            mode=gnmi_pb2.SubscriptionList.Mode.STREAM,
            encoding=gnmi_pb2.Encoding.PROTO,
            subscription=subscriptions,
        )
    )


async def request_generator(subscribe_request: gnmi_pb2.SubscribeRequest):
    """
    gNMI Subscribe のリクエストストリームを生成

    gNMI では最初に SubscribeRequest を送信してからレスポンスをストリーミング受信する。
    このジェネレータはリクエストを1回だけ yield する。

    Args:
        subscribe_request: gNMI購読リクエスト

    Yields:
        SubscribeRequest
    """
    yield subscribe_request


def extract_telemetry_value(typed_value) -> str:
    """
    gNMI レスポンスの値フィールドから実際の値を抽出

    gNMI の値は TypedValue 構造体で複数の型をサポートしており、
    どの型が設定されているかを判定して抽出する

    Args:
        typed_value: gNMI TypedValue オブジェクト

    Returns:
        文字列形式の値。対応する型がない場合は str(typed_value)
    """
    if typed_value.HasField("json_ietf_val"):
        return typed_value.json_ietf_val.decode('utf-8')
    elif typed_value.HasField("string_val"):
        return typed_value.string_val
    elif typed_value.HasField("int_val"):
        return str(typed_value.int_val)
    elif typed_value.HasField("uint_val"):
        return str(typed_value.uint_val)
    elif typed_value.HasField("bytes_val"):
        return typed_value.bytes_val.hex()
    else:
        return str(typed_value)


def path_to_string(path_elements) -> str:
    """
    gNMI PathElem のリストをパス文字列に変換

    例: [PathElem(name="a"), PathElem(name="b")] -> "a/b"

    Args:
        path_elements: PathElem のイテラブル

    Returns:
        スラッシュ区切りのパス文字列
    """
    return "/".join([elem.name for elem in path_elements])


def is_on_change_update(path_str: str) -> bool:
    """
    パス文字列が ON_CHANGE 対象パスかを判定

    Args:
        path_str: パス文字列（"elem1/elem2/..." 形式）

    Returns:
        True: ON_CHANGE パス / False: 通常のパス
    """
    for on_change_path in ON_CHANGE_PATHS:
        # ON_CHANGE_PATHS の " ON_CHANGE" 部分を除去して比較
        clean_on_change_path = on_change_path.replace(" ON_CHANGE", "").strip()
        # 簡易的なマッチング（実運用ではより厳密なパターンマッチング推奨）
        if "subinterface" in path_str and "ifindex" in path_str:
            return True

    return False


def extract_interface_info(path_elements) -> Dict[str, str]:
    """
    gNMI パス要素からインターフェース情報を抽出

    例: interfaces/interface[name=eth0]/subinterfaces/subinterface[index=0]/state/ifindex
    -> {'interface': 'eth0', 'subinterface_index': '0', 'leaf': 'ifindex'}

    Args:
        path_elements: PathElem のリスト

    Returns:
        抽出されたインターフェース情報の辞書
    """
    info = {
        'interface': None,
        'subinterface_index': None,
        'leaf': None,
        'full_path': '/'.join([elem.name for elem in path_elements])
    }

    for elem in path_elements:
        if elem.name == "interface" and elem.key:
            info['interface'] = elem.key.get('name', 'unknown')
        elif elem.name == "subinterface" and elem.key:
            info['subinterface_index'] = elem.key.get('index', 'unknown')

    # 最後の要素がリーフ（値）の属性名
    if path_elements:
        info['leaf'] = path_elements[-1].name

    return info


def format_event_details(
    host: str,
    prefix_path: str,
    path_str: str,
    current_value: str,
    previous_value: Optional[str],
    interface_info: Dict[str, str],
    timestamp: float
) -> str:
    """
    ON_CHANGE イベントの詳細情報をフォーマット

    Args:
        host: ホストアドレス
        prefix_path: プレフィックスパス
        path_str: 更新されたパス
        current_value: 現在の値
        previous_value: 前の値
        interface_info: インターフェース情報
        timestamp: タイムスタンプ

    Returns:
        フォーマット済みの詳細ログ文字列
    """
    timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))

    details_lines = []
    details_lines.append("=" * 80)

    details_lines.append(f"[EVENT] ON_CHANGE Detection on {host}")
    details_lines.append(f"Timestamp: {timestamp_str}")

    # インターフェース情報
    if interface_info['interface']:
        details_lines.append(f"Interface: {interface_info['interface']}")
    if interface_info['subinterface_index']:
        details_lines.append(f"Subinterface Index: {interface_info['subinterface_index']}")

    # 属性情報
    if interface_info['leaf']:
        details_lines.append(f"Attribute: {interface_info['leaf']}")

    # パス情報
    details_lines.append(f"Full Path: /{prefix_path}/{path_str}")

    # 値の変更
    if previous_value is not None:
        details_lines.append(f"Previous Value: {previous_value}")
        details_lines.append(f"Current Value:  {current_value}")
    else:
        details_lines.append(f"Initial Value: {current_value}")

    details_lines.append("=" * 80)

    return "\n".join(details_lines)


def format_data_table(records: list) -> str:
    """
    テレメトリレコードのリストをテーブル形式にフォーマット

    Args:
        records: テレメトリレコード（辞書）のリスト

    Returns:
        テーブル形式のフォーマット済み文字列
    """
    if not records:
        return ""

    # カラムヘッダー
    header = [
        "Host",
        "Path",
        "Value",
        "Type",
        "Timestamp"
    ]

    # データ行を準備
    rows = []
    for record in records:
        event_type = "EVENT" if record.get('is_event', False) else "DATA"
        timestamp_str = time.strftime(
            '%H:%M:%S',
            time.localtime(record['timestamp'])
        )

        rows.append([
            record['host'],
            record['path'][:30],  # パスを30文字に制限
            str(record['value'])[:20],  # 値を20文字に制限
            event_type,
            timestamp_str
        ])

    # テーブル幅を計算
    col_widths = [
        max(len(header[i]), max(len(row[i]) for row in rows))
        for i in range(len(header))
    ]

    # テーブル行を構築
    table_lines = []

    # ヘッダー行
    header_line = " | ".join(
        header[i].ljust(col_widths[i]) for i in range(len(header))
    )
    table_lines.append(header_line)
    table_lines.append("-" * len(header_line))

    # データ行
    for row in rows:
        data_line = " | ".join(
            row[i].ljust(col_widths[i]) for i in range(len(row))
        )
        table_lines.append(data_line)

    return "\n".join(table_lines)


def format_processing_summary(
    total_records: int,
    event_count: int,
    processing_time_sec: float
) -> str:
    """
    データ処理のサマリーをフォーマット

    Args:
        total_records: 処理したレコード数
        event_count: ON_CHANGE イベント数
        processing_time_sec: 処理にかかった時間（秒）

    Returns:
        フォーマット済みのサマリー文字列
    """
    summary_lines = [
        "=" * 80,
        f"Data Processing Summary",
        f"  Total Records:  {total_records}",
        f"  Events (ON_CHANGE): {event_count}",
        f"  Normal Data:    {total_records - event_count}",
        f"  Processing Time: {processing_time_sec:.3f}s",
        f"  Throughput:     {total_records / processing_time_sec:.1f} records/sec",
        "=" * 80,
    ]

    return "\n".join(summary_lines)


# ============================================================================
# メインロジック
# ============================================================================

async def data_processor(
    data_queue: asyncio.Queue,
    metrics: CollectorMetrics,
    shutdown_event: asyncio.Event
) -> None:
    """
    テレメトリデータをキューから取り出してバッチ処理し、画面に表示する非同期タスク

    動作:
    1. キューからデータを取り出す
    2. バッファにため込む
    3. 一定サイズ (DATA_BATCH_SIZE_FOR_WRITE) に達したら処理・表示
    4. shutdown_event が set されたら終了

    Args:
        data_queue: テレメトリデータのasyncio.Queue
        metrics: メトリクス記録オブジェクト
        shutdown_event: シャットダウンシグナル
    """
    logger.info("Data Processor task started.")
    data_buffer = []
    batch_number = 0

    try:
        while not shutdown_event.is_set():
            try:
                # タイムアウト付きでキューからデータ取得
                # shutdown_event を定期的にチェックするため、タイムアウトを設定
                data = await asyncio.wait_for(
                    data_queue.get(),
                    timeout=DATA_PROCESSOR_TIMEOUT_SEC
                )
            except asyncio.TimeoutError:
                # タイムアウト時：バッファが溜まっていれば処理
                if data_buffer:
                    logger.info(f"Processing {len(data_buffer)} records (timeout flush).")
                    data_buffer = []
                continue

            data_buffer.append(data)

            # ノンブロッキングで追加データを取得（バッチ処理の効率化）
            while not data_queue.empty() and len(data_buffer) < DATA_BUFFER_FETCH_LIMIT:
                try:
                    data_buffer.append(data_queue.get_nowait())
                except asyncio.QueueEmpty:
                    break

            # バッファが一定サイズに達したら処理・表示
            if len(data_buffer) >= DATA_BATCH_SIZE_FOR_WRITE:
                batch_number += 1
                start_time = time.time()

                # ========================================================
                # 1. データ処理（メトリクス記録など）
                # ========================================================
                event_count = 0
                for record in data_buffer:
                    metrics.record_data(record['host'])
                    if record.get('is_event', False):
                        event_count += 1

                # ========================================================
                # 2. 画面表示
                # ========================================================
                processing_time = time.time() - start_time

                # バッチ情報ヘッダー
                display_lines = [
                    "",
                    "=" * 80,
                    f"[BATCH #{batch_number}] Data Processing Report",
                    f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                    "=" * 80,
                ]

                # テーブル表示
                data_table = format_data_table(data_buffer)
                if data_table:
                    display_lines.append(data_table)

                # サマリー表示
                summary = format_processing_summary(
                    total_records=len(data_buffer),
                    event_count=event_count,
                    processing_time_sec=processing_time
                )
                display_lines.append("")
                display_lines.append(summary)

                # 画面出力
                print("\n".join(display_lines))

                # バッファクリア
                data_buffer = []

            data_queue.task_done()

    except asyncio.CancelledError:
        logger.warning("Data Processor task cancelled.")
    except Exception as e:
        logger.error(f"Data Processor failed: {e}")
    finally:
        logger.info("Data Processor task stopped.")


async def collector(
    host: str,
    port: int,
    user: str,
    password: str,
    data_queue: asyncio.Queue,
    metrics: CollectorMetrics,
    shutdown_event: asyncio.Event
) -> None:
    """
    単一ホストからgNMI購読でテレメトリを継続的に収集する非同期タスク

    動作:
    1. gRPCチャネルを確立
    2. gNMI Subscribe RPC でストリーミング開始
    3. レスポンスを処理してキューにデータを投入
    4. 接続エラーで落ちた場合は指数バックオフで再接続
    5. shutdown_event が set されたら終了

    Args:
        host: 接続先ホストアドレス
        port: gNMIサーバポート
        user: ユーザ名
        password: パスワード
        data_queue: データ投入先キュー
        metrics: メトリクス記録オブジェクト
        shutdown_event: シャットダウンシグナル
    """
    retry_count = 0
    last_success_time = time.time()

    while not shutdown_event.is_set():
        channel = None

        try:
            # ============================================================
            # 1. gRPCチャネル作成
            # ============================================================
            channel_options = [
                ('grpc.max_connection_idle_ms', 60000),
                ('grpc.keepalive_time_ms', GRPC_KEEPALIVE_TIME_SEC * 1000),
                ('grpc.keepalive_timeout_ms', GRPC_KEEPALIVE_TIMEOUT_SEC * 1000),
            ]
            channel = grpc.aio.insecure_channel(
                f"{host}:{port}",
                options=channel_options
            )
            stub = gnmi_pb2_grpc.gNMIStub(channel)

            # 認証メタデータ（基本認証）
            auth_metadata = [
                ("username", user),
                ("password", password),
            ]

            # ============================================================
            # 2. gNMI購読リクエスト構築
            # ============================================================
            subscribe_request = build_gnmi_subscription_request()

            logger.info(f"[{host}] Connecting... (attempt {retry_count + 1})")

            # ============================================================
            # 3. Subscribe RPC 実行 + レスポンス処理
            # ============================================================
            request_stream = request_generator(subscribe_request)

            async for response in stub.Subscribe(request_stream, metadata=auth_metadata):

                logger.debug(f"[{host}] Received gNMI response.")

                # ========================================================
                # 3a. Sync Response: 購読初期化完了
                # ========================================================
                if response.HasField("sync_response"):
                    logger.info(f"[{host}] Sync response received.")
                    retry_count = 0
                    last_success_time = time.time()

                # ========================================================
                # 3b. Error Response: エラー通知
                # ========================================================
                elif response.HasField("error"):
                    error_code = response.error.code
                    error_message = response.error.message
                    logger.error(f"[{host}] gNMI Error: Code={error_code}, Message={error_message}")

                    if error_code != 0:
                        break

                # ========================================================
                # 3c. Update Response: テレメトリデータ更新
                # ========================================================
                elif response.HasField("update"):
                    update = response.update
                    logger.debug(f"[{host}] Update response received.")

                    timestamp_sec = update.timestamp / 1e9
                    prefix_path = ""
                    if update.prefix:
                        prefix_path = path_to_string(update.prefix.elem)

                    # Delete 処理
                    for delete_path in update.delete:
                        delete_path_str = path_to_string(delete_path.elem)
                        logger.debug(
                            f"[{host}] Deleted: /{prefix_path}/{delete_path_str}"
                        )

                    # Update 処理（実際のテレメトリデータ）
                    for update_value in update.update:
                        path_str = path_to_string(update_value.path.elem)
                        value_str = extract_telemetry_value(update_value.val)

                        # ================================================
                        # ON_CHANGE イベント検知：詳細情報を表示
                        # ================================================
                        if is_on_change_update(path_str):
                            metrics.record_on_change_event(host)

                            value_key = f"{host}:{prefix_path}/{path_str}"
                            previous_value = metrics.get_previous_value(value_key)

                            # インターフェース情報抽出
                            interface_info = extract_interface_info(
                                update_value.path.elem
                            )

                            # デバッグログ：current_value と previous_value を確認
                            logger.debug(f"[DEBUG] value_key={value_key}, prev={previous_value}, curr={value_str}")

                            # 詳細ログ出力
                            event_details = format_event_details(
                                host=host,
                                prefix_path=prefix_path,
                                path_str=path_str,
                                current_value=value_str,
                                previous_value=previous_value,
                                interface_info=interface_info,
                                timestamp=timestamp_sec
                            )
                            logger.warning("\n" + event_details)

                            # 現在の値を保存
                            metrics.store_previous_value(value_key, value_str)
                        else:
                            logger.info(
                                f"[{host}] Updated: /{prefix_path}/{path_str} = {value_str}"
                            )

                        # テレメトリレコード作成
                        telemetry_record = {
                            'host': host,
                            'path': path_str,
                            'value': value_str,
                            'timestamp': timestamp_sec,
                            'received_at': time.time(),
                            'is_event': is_on_change_update(path_str)
                        }

                        # キューに投入（バックプレッシャー対応）
                        if data_queue.full():
                            await data_queue.put(telemetry_record)
                        else:
                            data_queue.put_nowait(telemetry_record)

                else:
                    logger.debug(f"[{host}] Unknown response type received.")

            logger.warning(f"[{host}] Stream ended normally. Attempting to reconnect.")

        # ============================================================
        # 例外処理
        # ============================================================

        except grpc.aio.AioRpcError as error:
            is_retryable = is_retryable_error(error)
            logger.error(f"[{host}] gRPC error: {error.code()} - {error.details()} (retryable={is_retryable})")
            metrics.record_error(host, str(error))

            if not is_retryable:
                logger.error(f"[{host}] Non-retryable gRPC error. Stopping collector.")
                break

        except asyncio.CancelledError:
            logger.warning(f"[{host}] Collection task cancelled.")
            break

        except Exception as error:
            logger.error(f"[{host}] Unexpected error: {error.__class__.__name__}: {error}")
            metrics.record_error(host, str(error))

        finally:
            # ============================================================
            # チャネルのクローズ
            # ============================================================
            if channel:
                try:
                    await asyncio.wait_for(channel.close(), timeout=GRPC_CONNECT_TIMEOUT_SEC)
                except asyncio.TimeoutError:
                    logger.warning(f"[{host}] Channel close timeout.")
                except Exception as close_error:
                    logger.debug(f"[{host}] Channel close error: {close_error}")

            # ============================================================
            # 再接続判定・待機
            # ============================================================
            # 成功時刻から RETRY_SUCCESS_RESET_TIME_SEC 経過していたら
            # リトライカウントをリセット（無限増加を防止）
            if time.time() - last_success_time > RETRY_SUCCESS_RESET_TIME_SEC:
                retry_count = 0

            # シャットダウン中でなければ再接続
            if not shutdown_event.is_set():
                backoff_delay = calculate_backoff_delay(retry_count)
                logger.info(
                    f"[{host}] Waiting {backoff_delay:.1f}s before retry "
                    f"(retry_count={retry_count})"
                )
                await asyncio.sleep(backoff_delay)
                retry_count += 1
                metrics.record_reconnect(host)


async def main() -> None:
    """
    メイン関数：全ての非同期タスクを管理・調整

    動作:
    1. ルータインベントリを読み込み（実運用ではDBから）
    2. データキュー、メトリクス、シャットダウンシグナルを初期化
    3. 各ルータごとに collector タスクを起動
    4. data_processor タスクを起動
    5. Ctrl+C でグレースフルシャットダウン
    """
    # ルータインベントリ（実装例）
    # 実運用では外部ファイルやDBから読み込む推奨
    router_inventory = [
        {
            "host": "192.168.254.1",
            "port": 9339,
            "user": "cisco",
            "password": "cisco123"
        },
        {
            "host": "192.168.254.2",
            "port": 9339,
            "user": "cisco",
            "password": "cisco123"
        },
    ]

    # 共有リソース初期化
    data_queue = asyncio.Queue(maxsize=DATA_QUEUE_MAX_SIZE)
    metrics = CollectorMetrics()
    shutdown_event = asyncio.Event()

    # データ処理タスク起動
    data_processor_task = asyncio.create_task(
        data_processor(data_queue, metrics, shutdown_event)
    )

    # 各ルータの収集タスク起動
    collection_tasks = []
    for router in router_inventory:
        task = asyncio.create_task(
            collector(
                host=router['host'],
                port=router['port'],
                user=router['user'],
                password=router['password'],
                data_queue=data_queue,
                metrics=metrics,
                shutdown_event=shutdown_event,
            )
        )
        collection_tasks.append(task)

    all_tasks = collection_tasks + [data_processor_task]
    logger.info(
        f"Started {len(collection_tasks)} collection task(s) "
        f"and 1 data processor task."
    )

    try:
        # 全タスク継続実行を待機
        # return_exceptions=True により、1つのタスク失敗で全体が止まらない
        await asyncio.gather(*all_tasks, return_exceptions=True)

    except KeyboardInterrupt:
        logger.info("Received Ctrl+C, initiating graceful shutdown...")

    finally:
        # ============================================================
        # グレースフルシャットダウン
        # ============================================================

        # 全タスクにシャットダウンシグナル送信
        shutdown_event.set()

        # 実行中のタスクをキャンセル
        for task in all_tasks:
            if not task.done():
                task.cancel()

        # 全タスクの終了を待機
        await asyncio.gather(*all_tasks, return_exceptions=True)

        # 最終レポート
        logger.info("All tasks stopped.")
        summary = metrics.get_summary()
        logger.info(f"Final Metrics: {summary}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program interrupted by user.")
