import websocket
import json
import uuid
import threading
import keyboard

TOKEN = None

PLUGIN_NAME = "WuLocalAI"
PLUGIN_DEVELOPER = "WuDeveloper"

def on_open(ws):
    print("连接成功")

    request = {
        "apiName": "VTubeStudioPublicAPI",
        "apiVersion": "1.0",
        "requestID": str(uuid.uuid4()),
        "messageType": "AuthenticationTokenRequest",
        "data": {
            "pluginName": PLUGIN_NAME,
            "pluginDeveloper": PLUGIN_DEVELOPER
        }
    }

    ws.send(json.dumps(request))


def on_message(ws, message):
    global TOKEN

    data = json.loads(message)

    print("\n收到消息:")
    print(json.dumps(data, indent=4, ensure_ascii=False))

    msg_type = data.get("messageType")

    # 第一步成功
    if msg_type == "AuthenticationTokenResponse":

        TOKEN = data["data"]["authenticationToken"]

        print("\n拿到Token:")
        print(TOKEN)

        auth_request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": str(uuid.uuid4()),
            "messageType": "AuthenticationRequest",
            "data": {
                "pluginName": PLUGIN_NAME,
                "pluginDeveloper": PLUGIN_DEVELOPER,
                "authenticationToken": TOKEN
            }
        }

        print("\n发送认证请求...")
        ws.send(json.dumps(auth_request))

    # 第二步成功
    elif msg_type == "AuthenticationResponse":

        authenticated = data["data"]["authenticated"]

        print("\n认证结果:", authenticated)

        if authenticated:
            print("认证成功！！！")
            request_express(ws)
        else:
            print("认证失败")

def request_express(ws):
    request = {
        "apiName": "VTubeStudioPublicAPI",
        "apiVersion": "1.0",
        "requestID": "SomeID",
        "messageType": "HotkeyTriggerRequest",
        "data": {
            "hotkeyID": "f9c5528eab6a4b1cb1189356c4d6a967"            
        }
    }

    ws.send(json.dumps(request))


def on_error(ws, error):
    print("错误:", error)


def on_close(ws, code, msg):
    print("连接关闭")

def keyboard_loop():
    while True:
        keyboard.wait("space")
        request_express(ws)


ws = websocket.WebSocketApp(
    "ws://127.0.0.1:8001",
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

threading.Thread(
    target=keyboard_loop,
    daemon=True
).start()

ws.run_forever()



