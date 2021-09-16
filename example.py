from PyWeComSpy import WeComSpy
from PyWeComSpy.constant import *
from PyWeComSpy import spy_pb2
from queue import Queue


my_response_queue = Queue()
spy = WeComSpy(response_queue=my_response_queue, key="ba31e59e9574332cdc7ee6198a725c70")


def pop_response():
    while True:
        data = my_response_queue.get()
        handle_response(data)


def handle_response(data):
    if data.type == WECHAT_CONNECTED:  # 微信接入
        print(f"企业微信客户端已接入 port:{data.port}")
    elif data.type == HEART_BEAT:  # 心跳
        pass
    elif data.type == WECHAT_LOGIN:  # 微信登录
        print("企业微信登录")
        spy.get_contacts()
    elif data.type == CONTACTS_LIST:
        contacts = spy_pb2.Contacts()
        contacts.ParseFromString(data.bytes)
        for contact in contacts.contact:
            print(contact.wxid, contact.nickname)
    else:
        print(data)


if __name__ == '__main__':
    pid = spy.run(r"C:\Program Files (x86)\WXWork\WXWork.exe")
    pop_response()