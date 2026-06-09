
from queue import Queue
import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(parent_dir))
import keyboard
import sounddevice as sd
import numpy as np
from silero_vad import load_silero_vad
import torch
from pyScripts.Listener.Faster_Whisper import audio_to_text


# 音频参数
FS = 16000
CHANNELS = 1
BLOCK_SIZE = 512  # Silero VAD 标准块大小（32ms @ 16kHz）

# VAD 参数
SPEECH_THRESHOLD = 0.5       # 语音概率阈值
SILENCE_DURATION = 1.0       # 静音持续多少秒后停止录音（容忍停顿）
MIN_SPEECH_DURATION = 0.1    # 最短有效语音时长，避免误触发

# 加载 Silero VAD 模型
print("⏳ 正在加载 VAD 模型...")
model = load_silero_vad()
print("✅ 模型加载完成，开始监听...")

# 状态变量
audio_buffer = []             # 录音数据累积
analysis_buffer = []          # VAD 分析用小缓冲区
is_speaking = False           # 当前是否在说话
silence_blocks = 0            # 连续静音块计数
speech_blocks = 0             # 连续语音块计数
SILENCE_BLOCKS_MAX = int(SILENCE_DURATION * FS / BLOCK_SIZE)
SPEECH_BLOCKS_MIN = int(MIN_SPEECH_DURATION * FS / BLOCK_SIZE)

result_queue = Queue()


def callback(indata, frames, time, status):
    global is_speaking, silence_blocks, speech_blocks, recording_finished, audio_buffer

    if status:
        print(f"⚠️ 状态异常: {status}")

    # 提取单声道音频
    audio_chunk = indata[:, 0].copy()

    # ---- 转换为 Tensor 后再送入 VAD ----
    audio_tensor = torch.from_numpy(audio_chunk)       
    speech_prob = model(audio_tensor, FS).item()

    if speech_prob > SPEECH_THRESHOLD:
        speech_blocks += 1
        silence_blocks = 0
        if not is_speaking and speech_blocks >= SPEECH_BLOCKS_MIN:
            is_speaking = True
            audio_buffer.clear()
            print("🎤 检测到语音，开始录音...")
    else:
        silence_blocks += 1
        speech_blocks = 0

    if is_speaking:
        audio_buffer.append(audio_chunk)
        if silence_blocks >= SILENCE_BLOCKS_MAX:
            is_speaking = False
            print("🛑 检测到持续静音，录音结束")
            if len(audio_buffer) > 0:
                audio_np = np.concatenate(audio_buffer, axis=0)
                result_queue.put(audio_np)        
                
                audio_buffer.clear()     
                silence_blocks = 0
                speech_blocks = 0

            # raise sd.CallbackStop()



# 创建并启动输入流
stream = sd.InputStream(
    channels=CHANNELS,
    samplerate=FS,
    blocksize=BLOCK_SIZE,
    callback=callback,
    dtype=np.float32,  # Silero VAD 需要 float32 格式
)

print("🔇 保持安静，说话时将自动开始录音...\n")
stream.start()

# ========== 主线程：从队列取数据 → 识别 → 打印 ==========
try:
    while True:        
        if keyboard.is_pressed("Esc"):
            print("中断操作")
            break

        try:
            audio_np = result_queue.get(timeout=0.2)   # 0.2 秒醒一次
        except:
            continue   # 没数据就回到循环顶部，重新检查 Esc

        duration = len(audio_np) / FS
        if duration < MIN_SPEECH_DURATION:
            print(f"⚠️ 录音 {duration:.1f} 秒过短，跳过\n")
            continue

        print(f"📝 录音时长: {duration:.1f} 秒，正在识别...")

        audio_float = audio_np.flatten().astype(np.float32)
        text = audio_to_text(audio_float)

        print("-" * 40 + "\n")

except KeyboardInterrupt:
    print("\n👋 退出")

stream.stop()
stream.close()



