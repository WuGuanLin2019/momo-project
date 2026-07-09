import requests
import io
import soundfile as sf

def cosy_tts(text):
    resp = requests.post("http://127.0.0.1:5002/tts", json={"text": text}, timeout=30)
    if resp.status_code == 200:
        audio_data, sample_rate = sf.read(io.BytesIO(resp.content))
        
        # return audio_data, sample_rate
    return None, None
