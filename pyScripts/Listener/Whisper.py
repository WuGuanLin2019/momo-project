from asyncio.windows_events import NULL
import sounddevice as sd
import numpy as np
import keyboard
import scipy.io.wavfile as wav
import whisper
import time

# 配置
FS = 16000  # 采样率
CHANNELS = 1  # 单声道
AUDIO_OUTPUT_FILE = "Temp/inputWords.wav"

print("加载Whisper模型...")
model = whisper.load_model("small")
print("模型加载完成。")

def record_until_space_released():
    print("按住空格开始录音...")
    audio_data = []

    # 等待按下空格
    keyboard.wait('space')
    print("录音开始...")

    def callback(indata, frames, time, status):
        audio_data.append(indata.copy())

    with sd.InputStream(channels=CHANNELS, samplerate=FS, callback=callback):
        # 持续录音直到空格松开
        while keyboard.is_pressed('space'):
            sd.sleep(100)

    print("录音结束，处理中...")

    # 拼接音频
    audio_np = np.concatenate(audio_data, axis=0)
    # wav.write(AUDIO_OUTPUT_FILE, FS, (audio_np * 32767).astype(np.int16))

    audio_float = audio_np.flatten().astype(np.float32)
    return audio_float

def update_fun(callBack):
    audio_float = record_until_space_released()
    result = model.transcribe(audio_float, language="zh")
    print("识别结果:", result["text"])
    if callBack is not None:
        return callBack(result["text"])
    print("\n——下一次录音——\n")