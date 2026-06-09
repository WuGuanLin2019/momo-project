import websocket
import json
import uuid
import threading
import time
from pydub import AudioSegment
import numpy as np
import simpleaudio as sa

# ----------------------------
# 配置部分
# ----------------------------
VTUBE_WS_URL = "ws://127.0.0.1:8001"
PLUGIN_NAME = "WuLocalAI"
PLUGIN_DEVELOPER = "WuDeveloper"
AUDIO_FILE = "output.wav"  # 替换为你的音频文件路径
MOUTH_PARAM = "PARAM_MOUTH_OPEN_Y"
FRAME_RATE = 60  # 每秒更新嘴型次数

TOKEN = None
ws_app = None


# ----------------------------
# WebSocket 相关
# ----------------------------
def send_mouth_param(ws, current_volume):
    """发送嘴型参数到 VTube Studio"""
    request = {
        "apiName": "VTubeStudioPublicAPI",
        "apiVersion": "1.0",
        "requestID": str(uuid.uuid4()),
        "messageType": "InjectParameterDataRequest",
        "data": {
            "faceFound": False,
            "mode": "set",
            "parameterValues": [{"id": "MouthOpen", "value": current_volume}],
        },
    }
    ws.send(json.dumps(request))


def on_open(ws):
    print("✅ WebSocket 已连接，发送 AuthenticationTokenRequest")
    ws.send(
        json.dumps(
            {
                "apiName": "VTubeStudioPublicAPI",
                "apiVersion": "1.0",
                "requestID": str(uuid.uuid4()),
                "messageType": "AuthenticationTokenRequest",
                "data": {
                    "pluginName": PLUGIN_NAME,
                    "pluginDeveloper": PLUGIN_DEVELOPER,
                },
            }
        )
    )


def on_message(ws, message):
    global TOKEN
    data = json.loads(message)
    msg_type = data.get("messageType")
    print("\n收到消息:")
    print(json.dumps(data, indent=4, ensure_ascii=False))

    if msg_type == "AuthenticationTokenResponse":
        TOKEN = data["data"]["authenticationToken"]
        print("🔑 拿到 Token:", TOKEN)

        # 发送认证请求
        auth_request = {
            "apiName": "VTubeStudioPublicAPI",
            "apiVersion": "1.0",
            "requestID": str(uuid.uuid4()),
            "messageType": "AuthenticationRequest",
            "data": {
                "pluginName": PLUGIN_NAME,
                "pluginDeveloper": PLUGIN_DEVELOPER,
                "authenticationToken": TOKEN,
            },
        }
        ws.send(json.dumps(auth_request))

    elif msg_type == "AuthenticationResponse":
        if data["data"].get("authenticated", False):
            print("✅ 认证成功，可以驱动嘴型了")
            # 开始音频播放和口型线程
            threading.Thread(
                target=play_audio_and_drive_mouth, args=(ws,), daemon=True
            ).start()
        else:
            print("❌ 认证失败")


def on_error(ws, error):
    print("❌ WebSocket 错误:", error)


def on_close(ws, code, msg):
    print("🔒 WebSocket 已关闭", code, msg)


# ----------------------------
# 音频处理和口型驱动
# ----------------------------
def play_audio_and_drive_mouth(ws):
    print("🎵 加载音频文件...")
    audio = AudioSegment.from_file(AUDIO_FILE)
    samples = np.array(audio.get_array_of_samples()).astype(np.float32)
    samples /= np.max(np.abs(samples))  # 归一化到 -1 ~ 1

    frame_size = int(len(samples) / (audio.duration_seconds * FRAME_RATE))
    volumes = []
    for i in range(0, len(samples), frame_size):
        frame = samples[i : i + frame_size]
        volumes.append(float(np.mean(np.abs(frame))))

    print(f"⚡ 总帧数: {len(volumes)}, 开始播放音频并驱动嘴型...")

    # 播放音频
    playback = sa.play_buffer(
        (samples * 32767).astype(np.int16),  # 转换回16位PCM
        num_channels=audio.channels,
        bytes_per_sample=2,
        sample_rate=audio.frame_rate,
    )

    # 按帧发送嘴型
    for v in volumes:
        send_mouth_param(ws, min(max(v * 1.5, 0), 1))  # 缩放0~1
        time.sleep(1 / FRAME_RATE)

    playback.wait_done()
    print("✅ 音频播放完成，嘴型驱动结束")


# ----------------------------
# 启动 WebSocket
# ----------------------------
if __name__ == "__main__":
    ws_app = websocket.WebSocketApp(
        VTUBE_WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws_app.run_forever()
