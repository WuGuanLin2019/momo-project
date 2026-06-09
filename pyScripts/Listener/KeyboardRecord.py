import keyboard
import sounddevice as sd
import numpy as np

FS = 16000  # 采样率

def record_until_space_released():
    print("按住空格开始录音...")
    audio_data = []

    # 等待按下空格
    keyboard.wait('space')
    print("录音开始...")

    def callback(indata, frames, time, status):
        audio_data.append(indata.copy())

    with sd.InputStream(channels=1, samplerate=FS, callback=callback):
        # 持续录音直到空格松开
        while keyboard.is_pressed('space'):
            sd.sleep(100)

    print("录音结束，处理中...")
    if len(audio_data) == 0:
        return None

    # 拼接音频
    audio_np = np.concatenate(audio_data, axis=0)
    # wav.write(AUDIO_OUTPUT_FILE, FS, (audio_np * 32767).astype(np.int16))

    audio_float = audio_np.flatten().astype(np.float32)
    return audio_float