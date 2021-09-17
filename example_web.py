from PyWeComSpy.service import SpyService
from flask.json import jsonify, request
from time import sleep
from flask_cors import CORS
import random
from queue import Queue
from threading import Thread


app = SpyService(__name__, key="ba31e59e9574332cdc7ee6198a725c70")
CORS(app, supports_credentials=True)  # 允许跨域
send_queue = Queue()


def send():
    while True:
        wxid, msg = send_queue.get()
        app.spy.send_text(wxid, msg)
        sleep(random.randint(3, 5))


t = Thread(target=send)
t.daemon = True
t.start()


@app.route("/send_text", methods=["GET", "POST"])
def send_text():
    nicknames = request.json["nicknames"]
    msg = request.json["msg"]
    for nickname in nicknames:
        wxid = app.nickname2wxid.get(nickname)
        send_queue.put((wxid, msg))
    return jsonify({"code": 1})


if __name__ == '__main__':
    app.run(host="0.0.0.0")
