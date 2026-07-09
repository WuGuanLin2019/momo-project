# from .Kokoro import text_to_audioData
# from Express.Moss import tts_synthesize
from Express.TTS_Client import request_audio_data


def ttsData(text) :
    return request_audio_data(text)