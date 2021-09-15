from PyWeComSpy.service import SpyService
from flask.json import jsonify
from time import sleep
from flask_cors import CORS
import random


app = SpyService(__name__, key="ba31e59e9574332cdc7ee6198a725c70")
CORS(app, supports_credentials=True)  # 允许跨域


@app.route("/send_text")
def send_text():
    # nicknames = request.json["nicknames"]
    # msg = request.json["msg"]
    nicknames = ["晨风", "720"]
    for nickname in nicknames:
        wxid = app.nickname2wxid.get(nickname)
        msg = "test"
        app.spy.send_text(wxid, msg)
        sleep(random.randint(3, 5))
    return jsonify({"code": 1})


if __name__ == '__main__':
    app.run()
