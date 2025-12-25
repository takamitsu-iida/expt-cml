"""
protoファイルをダウンロード
https://github.com/openconfig/gnmi

pip install grpcio grpcio-tools



python -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. gnmi.proto

"""

import grpc
from concurrent import futures
import gnmi_pb2
import gnmi_pb2_grpc

class GNMIServicer(gnmi_pb2_grpc.gNMIServicer):
    def Capabilities(self, request, context):
        # サーバーの能力を定義
        response = gnmi_pb2.CapabilityResponse()
        response.supported_models.add(name="openconfig-interfaces", organization="openconfig", version="0.1.0")
        response.supported_encodings.append(gnmi_pb2.JSON)
        response.gNMI_version = "0.8.0"
        return response

    def Get(self, request, context):
        # データ取得のリクエスト処理
        response = gnmi_pb2.GetResponse()
        # ここでリクエストされたpathに応じた値を詰め込む処理を書く
        return response

    def Subscribe(self, request_iterator, context):
        # ストリーミング処理
        for request in request_iterator:
            # クライアントからのSubscribeリクエストに応じて
            # yield で gnmi_pb2.SubscribeResponse を返し続ける
            pass

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    gnmi_pb2_grpc.add_gNMIServicer_to_server(GNMIServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("gNMI Server started on port 50051")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()