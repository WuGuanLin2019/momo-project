import numpy as np
import simpleaudio as sa
import requests
import io
import soundfile as sf

TTS_PORT = 5004

def request_audio_data(text):
    #使用melo
    resp = requests.post(f"http://127.0.0.1:{TTS_PORT}/tts", json={"text": text}, timeout=180)
    print(f"[tts_client] status={resp.status_code}, content-type={resp.headers.get('content-type')}, len={len(resp.content)}")
    
    if resp.status_code != 200:
        print(f"[tts_client] 服务端错误: {resp.text[:200]}")
        return None, None

    try:
        audio_data, sample_rate = sf.read(io.BytesIO(resp.content))
        return audio_data, sample_rate
    except Exception as e:
        print(f"[tts_client] 解码音频失败: {e}")
        print(f"[tts_client] 前200字节: {resp.content[:200]}")
        return None, None
