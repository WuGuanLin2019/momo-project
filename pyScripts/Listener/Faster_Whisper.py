from faster_whisper import WhisperModel

# 配置
FS = 16000  # 采样率
CHANNELS = 1  # 单声道
AUDIO_OUTPUT_FILE = "Temp/inputWords.wav"


print("加载Whisper模型...")
model = WhisperModel(
    "medium",
    device="cuda",
    compute_type="float16"
)
print("模型加载完成。")


def audio_to_text(audio_float):
    if audio_float is None:
        return
    
    segments, info = model.transcribe(
        audio_float,
        language="zh",
        beam_size=5,
        vad_filter=True,
        initial_prompt="以下内容是普通话或者粤语。"
    )
    text = ""

    text = "".join(segment.text for segment in segments)

    text = text.strip()
    print("识别结果:", text)
    # print("\n——下一次录音——\n")
    return text

# if __name__ == "__main__":
#     while True:
#         update_fun()