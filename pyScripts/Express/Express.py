import queue
import threading
from Body.VTube.VTube import VTubeClient
import numpy as np
from Core.State import GenerationState, SpeakTask
import simpleaudio as sa
from .TTSMgr import ttsData

MomoVTube = VTubeClient()
MomoVTube.start()

def playVoice(audio_data, sample_rate):
    if audio_data is None:
        return

    if audio_data.dtype != np.int16:
        audio_data = (audio_data * 32767).astype(np.int16)

    playObject = sa.play_buffer(audio_data, 1, 2, sample_rate)        
    return playObject

def loop(to_speak_queue:queue.Queue[SpeakTask], pipelineState:GenerationState, event_is_talking:threading.Event):
    while True:
        speak_task = to_speak_queue.get()
        if not pipelineState.check_is_current_generation(speak_task.generation_id):
            continue

        if speak_task.text.strip() == "":
            continue

        try:
            audio_data, sample_rate = ttsData(speak_task.text)
        except Exception as e:
            print(f"tts错误：{e}")
            continue

        def check_generate_break():
            return not pipelineState.check_is_current_generation(speak_task.generation_id)

        event_is_talking.set()
        MomoVTube.drive_mouth(audio_data, sample_rate, playVoice, check_generate_break)
        event_is_talking.clear()

