import os
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
import logging
from . import spy_pb2
import subprocess
from queue import Queue
from uuid import uuid4
from .constant import *
import sys


if not sys.version >= "3.8":
    logging.error("微信版本过低，请使用Python3.8.x或更高版本")
    exit()


class WeComSpy:
    def __init__(self, response_queue=None, key: str = None, logger: logging.Logger = None):
        self.__key = key
        # 日志模块
        if isinstance(logger, logging.Logger):
            # 使用自定义logger
            self.__logger = logger
        else:
            # 使用默认logger
            self.__logger = logging.getLogger(__file__)
            formatter = logging.Formatter('%(asctime)s [%(threadName)s] %(levelname)s: %(message)s')
            sh = logging.StreamHandler()
            sh.setFormatter(formatter)
            sh.setLevel(logging.DEBUG)
            self.__logger.addHandler(sh)
            self.__logger.setLevel(logging.DEBUG)
        # response存放队列
        if isinstance(response_queue, Queue):
            self.__response_queue = response_queue
        else:
            raise Exception("response_queue must be Queue")
        self.pids = []
        self.port2client = dict()
        host = "127.0.0.1"
        port = 9527
        self.__socket_server = socket(AF_INET, SOCK_STREAM)
        self.__socket_server.bind((host, port))
        self.__socket_server.listen(1)
        t_start_server = Thread(target=self.__start_server)
        t_start_server.daemon = True
        t_start_server.name = "spy"
        t_start_server.start()
        current_path = os.path.split(os.path.abspath(__file__))[0]
        helper_path = os.path.join(current_path, "SpyK.exe")
        if not os.path.exists(helper_path):
            self.__logger.error("请检查文件 SpyK.exe 是否被误删")
            exit(-1)
        subprocess.Popen(helper_path)

    def __start_server(self):
        while True:
            socket_client, client_address = self.__socket_server.accept()
            self.port2client[client_address[1]] = socket_client
            self.__logger.debug(f"A WeChat process from {client_address} successfully connected")
            if self.__key:
                self.set_commercial(self.__key, port=client_address[1])
            t_socket_client_receive = Thread(target=self.receive, args=(socket_client, client_address))
            t_socket_client_receive.name = f"wechat {client_address}"
            t_socket_client_receive.daemon = True
            t_socket_client_receive.start()

    def receive(self, socket_client: socket, client_address: tuple):
        recv_bytes = b""
        data_size = 0
        while True:
            try:
                _bytes = socket_client.recv(4096)
            except Exception as e:
                self.port2client.pop(client_address[1])
                response = spy_pb2.Response()
                response.type = WECHAT_DISCONNECT
                response.port = client_address[1]
                self.__response_queue.put(response)
                return self.__logger.warning(f"The WeChat process has disconnected: {e}")
            recv_bytes += _bytes
            while True:
                if not data_size:
                    if len(recv_bytes) > 3:
                        data_size = int.from_bytes(recv_bytes[:4], "little")
                    else:
                        break
                elif data_size <= len(recv_bytes) - 4:
                    response = spy_pb2.Response()
                    response.ParseFromString(recv_bytes[4: data_size + 4])
                    response.port = client_address[1]
                    self.__response_queue.put(response)
                    recv_bytes = recv_bytes[data_size + 4:]
                    data_size = 0
                else:
                    break

    def __send(self, request: spy_pb2.Request, port: int = 0, _id: str = None):
        if not port and self.port2client:
            socket_client: socket = list(self.port2client.values())[0]
        elif not (socket_client := self.port2client.get(port)):
            self.__logger.error(f"Failure to find socket client by port:{port}")
            return False
        request.id = _id or uuid4().__str__()
        data = request.SerializeToString()
        data_length_bytes = int.to_bytes(len(data), length=4, byteorder="little")
        try:
            socket_client.send(data_length_bytes + data)
            return True
        except Exception as e:
            self.__logger.warning(f"The WeChat process {port} has disconnected: {e}")
            return False

    def run(self, wechat: str):
        sp = subprocess.Popen(wechat)
        self.pids.append(sp.pid)
        return sp.pid

    def set_commercial(self, key: str, port: int = 0, _id: str = None):
        request = spy_pb2.Request()
        request.type = PROFESSIONAL_KEY
        request.bytes = bytes(key, encoding="utf8")
        return self.__send(request, port, _id)

    def get_contacts(self, port: int = 0, _id: str = None):
        request = spy_pb2.Request()
        request.type = GET_CONTACTS_LIST
        return self.__send(request, port, _id)

    def get_group_members(self, wxid, port: int = 0, _id: str = None):
        request = spy_pb2.Request()
        request.type = GET_CONTACT_DETAILS
        request.bytes = bytes(wxid, encoding="utf8")
        return self.__send(request, port, _id)

    def send_text(self, wxid: str, text: str, at_wxid: str = "", port: int = 0, _id: str = None):
        request = spy_pb2.Request()
        request.type = SEND_TEXT
        text_message = spy_pb2.TextMessage()
        text_message.wxid = wxid
        text_message.wxidAt = at_wxid
        text_message.text = text
        request.bytes = text_message.SerializeToString()
        return self.__send(request, port, _id)