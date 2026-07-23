import numpy as np
import simpleaudio as sa
import requests
import io
import soundfile as sf
from Listener.SileroVAD import AudioBufferData
from Utils.Tool import clearQueue

STT_PORT = 5003

def request_audio_text(audio_data: AudioBufferData)->tuple[str|None,bool|None]:
    abData = audio_data.audio_buffer
    if abData.size == 0 and not audio_data.is_done:
        return None, None

    # print(f"audio_data:{audio_data}")
    resp = requests.post(
        f"http://127.0.0.1:{STT_PORT}/stt/fun",
        json={"audio_buffer": abData.tolist(), "is_done": audio_data.is_done},
        timeout=10,
    )
    # print(
    #     f"[stt_client] status={resp.status_code}, content-type={resp.headers.get('content-type')}, len={len(resp.content)}"
    # )

    if resp.status_code != 200:
        print(f"[stt_client] 服务端错误: {resp.text[:200]}")
        return None, None

    try:
        data = resp.json()
        txt, is_done = data[0], data[1]
        return txt, is_done
    except Exception as e:
        print(f"[stt_client] 语音识别失败: {e}")
        print(f"[stt_client] 前200字节: {resp.content}")
        return None, None


def interage_audio_text():
    resp = requests.post(f"http://127.0.0.1:{STT_PORT}/stt/interage", timeout=10)
    print(
        f"[stt_client] 语音识别中断 status={resp.status_code}, content-type={resp.headers.get('content-type')}, len={len(resp.content)}"
    )

def STT_Loop(abDatas,input_text_queue,check_generate_break):
    current_input_txt = ""
    while True:
        if check_generate_break():
            clearQueue(input_text_queue)
            interage_audio_text()
            continue

        abData = abDatas.get()
        audio_str,is_done = request_audio_text(abData)

        if audio_str:
            current_input_txt = current_input_txt + audio_str

        if not is_done:
            continue

        print(f"语音流式识别结果：{current_input_txt}")
        input_text_queue.put(current_input_txt)

        if is_done:
            current_input_txt = ""