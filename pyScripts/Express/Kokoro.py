from Utils.Timer import SmallTimer
from kokoro import KPipeline
import numpy as np
import librosa
import emoji

print("加载Kokoro...")
pipeline = KPipeline(
	lang_code='z',
 	repo_id= "hexgrad/Kokoro-82M",
    device="cuda",
)

SAMPLE_RATE = 24000

def trim_excess_trailing_silence(audio:np.float32, sr, top_db=30, max_allowed_silence=0.0):
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
    if text is None or text == "":
        return None, None

    text = emoji.replace_emoji(text, replace='')  # 直接删除
    text = text.replace('\n', '。')     #换行时语音会截断

    # 生成音频，只取第一个结果（通常只有一个）
    generator = pipeline(text, voice='zf_xiaoxiao')

    with SmallTimer("tts"):
        for _, _, audio in generator:
            if hasattr(audio, 'cpu'):
                # with SmallTimer("cpu tts"):
                audio = audio.cpu()      # 确保在 CPU 上
            if hasattr(audio, 'numpy'):
                # with SmallTimer("numpy tts"):
                audio = audio.numpy()    # 转成 numpy
            # with SmallTimer("np asType tts"):
            audio = audio.astype(np.float32)

            trimmed_audio = trim_excess_trailing_silence(audio,SAMPLE_RATE)
            return trimmed_audio, SAMPLE_RATE   # (audio_data, sample_rate)

    return None, None

if __name__ == "__main__":
    text_to_audioData("介绍一下你自己")