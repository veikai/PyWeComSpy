from flask import Flask
from ..spy import WeComSpy
from queue import Queue
from threading import Thread
from ..spy_pb2 import Contacts
from ..constant import *
import time


class SpyService(Flask):
    def __init__(self, import_name,
                 static_url_path=None,
                 static_folder="static",
                 static_host=None,
                 host_matching=False,
                 subdomain_matching=False,
                 template_folder="templates",
                 instance_path=None,
                 instance_relative_config=False,
                 root_path=None,
                 key=None):
        self.last_client_count = 0
        self.response_queue = Queue()
        self.client2pid = dict()
        self.client2wxid = dict()
        self.client2login = dict()
        self.nickname2wxid = dict()
        self.spy = WeComSpy(response_queue=self.response_queue, key=key)
        super().__init__(import_name,
                         static_url_path=static_url_path,
                         static_folder=static_folder,
                         static_host=static_host,
                         host_matching=host_matching,
                         subdomain_matching=subdomain_matching,
                         template_folder=template_folder,
                         instance_path=instance_path,
                         instance_relative_config=instance_relative_config,
                         root_path=root_path)
        t = Thread(target=self.parse)
        t.setDaemon(True)
        t.start()
        self.spy.run(r"C:\Program Files (x86)\WXWork\WXWork.exe")

    def parse(self):
        while True:
            data = self.response_queue.get()
            if data.type == WECHAT_CONNECTED:
                print(data.port)
                self.client2pid[data.port] = data.pid
                self.client2login[data.port] = "0"
            elif data.type == WECHAT_DISCONNECT:
                self.last_client_count -= 1
            elif data.type == WECHAT_LOGIN:
                self.client2login[data.port] = "1"
                t = Thread(target=self.refresh_contacts)
                t.daemon = True
                t.start()
            elif data.type == WECHAT_LOGOUT:
                self.client2login[data.port] = "0"
            elif data.type != HEART_BEAT:
                if data.type == CONTACTS_LIST:
                    contacts = Contacts()
                    contacts.ParseFromString(data.bytes)
                    for contact in contacts.contact:
                        self.nickname2wxid[contact.nickname] = contact.wxid
                    print(self.nickname2wxid)

    def refresh_contacts(self):
        while True:
            print(time.strftime("%Y-%m-%d %H:%M:%S"), "refresh contacts")
            self.spy.get_contacts()
            time.sleep(5)
