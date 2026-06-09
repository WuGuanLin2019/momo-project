from asyncio.windows_events import NULL
from kokoro import KPipeline
import numpy as np
import librosa
import emoji

print("加载Kokoro...")
pipeline = KPipeline(
	lang_code='z',
 	repo_id= "hexgrad/Kokoro-82M"
)

AUDIO_OUTPUT_FILE = "Temp/output.wav"
SAMPLE_RATE = 24000

def trim_excess_trailing_silence(audio, sr, top_db=30, max_allowed_silence=0.0):
    # max_allowed_silence: 允许保留的最大尾部静音长度(秒)
    
    # 1. 先用 librosa 获取有效音频的起止索引
    trimmed_audio, (start, end) = librosa.effects.trim(audio, top_db=top_db)
    
    # 2. 计算原本尾部静音的长度
    original_trailing_silence = len(audio) - end
    
    # 3. 判断如果尾部静音过长，则进行裁剪
    target_trailing_samples = int(sr * max_allowed_silence)
    if original_trailing_silence > target_trailing_samples:
        return audio[:end + target_trailing_samples]
    return audio

def text_to_audioData(text):
    if text == NULL or text == "":
        return

    text = emoji.replace_emoji(text, replace='')  # 直接删除

    # 生成音频，只取第一个结果（通常只有一个）
    generator = pipeline(text, voice='zf_xiaoxiao')
    for _, _, audio in generator:
        if hasattr(audio, 'cpu'):
            audio = audio.cpu()      # 确保在 CPU 上
        if hasattr(audio, 'numpy'):
            audio = audio.numpy()    # 转成 numpy
        audio = audio.astype(np.float32)

        trimmed_audio = trim_excess_trailing_silence(audio,SAMPLE_RATE)
        return trimmed_audio, SAMPLE_RATE   # (audio_data, sample_rate)

    return None, None