from queue import Empty, Queue
import threading
import sounddevice as sd
import numpy as np
from silero_vad import load_silero_vad
import torch
from collections import deque
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.font_manager import FontProperties
import platform

matplotlib.use('TkAgg')

from Core.State import GenerationState

# ==================== 中文字体修复 ====================
def setup_chinese_font():
    """配置 Matplotlib 中文字体"""
    system = platform.system()
    fonts_to_try = []

    if system == 'Windows':
        fonts_to_try = ['Microsoft YaHei', 'SimHei', 'KaiTi', 'FangSong']
    elif system == 'Darwin':  # macOS
        fonts_to_try = ['PingFang SC', 'Heiti SC', 'STHeiti', 'Apple LiGothic']
    else:  # Linux
        fonts_to_try = ['WenQuanYi Micro Hei', 'WenQuanYi Zen Hei', 'Noto Sans CJK SC', 'Droid Sans Fallback']

    available_fonts = [f.name for f in matplotlib.font_manager.fontManager.ttflist]

    chosen_font = None
    for font_name in fonts_to_try:
        if font_name in available_fonts:
            chosen_font = font_name
            break

    if chosen_font:
        plt.rcParams['font.sans-serif'] = [chosen_font, 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        print(f"✅ 使用中文字体: {chosen_font}")
        return chosen_font
    else:
        print("⚠️ 未找到中文字体，中文可能无法正常显示")
        return None

chinese_font = setup_chinese_font()

# ==================== 参数配置 ====================
FS = 16000
CHANNELS = 1
BLOCK_SIZE = 512

# ---- VAD 参数 ----
SPEECH_THRESHOLD = 0.8          # 语音概率阈值
SILENCE_DURATION = 0.8          # 静音持续多久停止录音
MIN_SPEECH_DURATION = 0.3       # 最短有效语音

# ✅ 新增：音量阈值（RMS）
VOLUME_THRESHOLD = 0.02         # RMS 下限，低于此音量视为静音/噪声

RING_MS = 500
RING_SIZE = int(FS * (RING_MS / 1000))

# 可视化参数
PLOT_HISTORY_SIZE = 200
PLOT_UPDATE_INTERVAL = 30

ring_buffer = deque(maxlen=RING_SIZE)

print("⏳ 正在加载 VAD 模型...")
model = load_silero_vad()
print("✅ 模型加载完成")

SILENCE_BLOCKS_MAX = int(SILENCE_DURATION * FS / BLOCK_SIZE)
SPEECH_BLOCKS_MIN = int(MIN_SPEECH_DURATION * FS / BLOCK_SIZE)


class AudioListener:
    def __init__(self, pipelineState: GenerationState, event_is_talking: threading.Event):
        self.result_queue = Queue()
        self.pipelineState = pipelineState
        self.event_is_talking = event_is_talking

        self.audio_buffer = []
        self.is_speaking = False
        self.silence_blocks = 0
        self.speech_blocks = 0

        # 可视化数据
        self.speech_probs = deque(maxlen=PLOT_HISTORY_SIZE)
        self.speech_states = deque(maxlen=PLOT_HISTORY_SIZE)

        # ✅ 新增：RMS 历史
        self.volume_rms_history = deque(maxlen=PLOT_HISTORY_SIZE)

        self.callback_count = 0
        self._needs_update = False
        self._update_lock = threading.Lock()

        # 初始化图表（主线程）
        self.setup_plot()

        self.stream = sd.InputStream(
            channels=CHANNELS,
            samplerate=FS,
            blocksize=BLOCK_SIZE,
            callback=self.callback,
            dtype=np.float32,
        )

        print("🔇 保持安静，说话且有足够音量时自动录音...")
        print(f"   音量阈值 RMS >= {VOLUME_THRESHOLD:.3f}\n")
        self.stream.start()

    def setup_plot(self):
        plt.ion()
        # 改为三行：概率曲线 + 音量曲线 + 状态表格
        self.fig, (self.ax1, self.ax2, self.ax3) = plt.subplots(3, 1, figsize=(12, 10),
                                                                 gridspec_kw={'height_ratios': [2, 2, 1]})

        # ---- 第一子图：语音概率 ----
        self.prob_line, = self.ax1.plot([], [], 'b-', linewidth=1.5, label='语音概率')
        self.threshold_line = self.ax1.axhline(
            y=SPEECH_THRESHOLD, color='r', linestyle='--', linewidth=1.5,
            label=f'VAD阈值 ({SPEECH_THRESHOLD})')
        self.ax1.set_xlim(0, PLOT_HISTORY_SIZE)
        self.ax1.set_ylim(-0.1, 1.1)
        self.ax1.set_ylabel('语音概率')
        self.ax1.set_title('Silero VAD + 音量检测')
        self.ax1.legend(loc='upper right')
        self.ax1.grid(True, alpha=0.3)

        # ---- 第二子图：音量 RMS ----
        self.vol_line, = self.ax2.plot([], [], 'g-', linewidth=1.5, label='RMS 音量')
        self.vol_threshold_line = self.ax2.axhline(
            y=VOLUME_THRESHOLD, color='orange', linestyle='--', linewidth=1.5,
            label=f'音量阈值 ({VOLUME_THRESHOLD:.3f})')
        self.ax2.set_xlim(0, PLOT_HISTORY_SIZE)
        self.ax2.set_ylim(-0.01, 0.2)  # RMS 通常在这个量级
        self.ax2.set_ylabel('RMS 音量')
        self.ax2.set_xlabel('时间 (帧)')
        self.ax2.legend(loc='upper right')
        self.ax2.grid(True, alpha=0.3)

        # ---- 第三子图：状态表格 ----
        self.ax3.axis('off')
        self.status_labels = ['语音概率', 'RMS 音量', '语音块数', '静音块数', '是否说话', '缓冲区大小']
        self.status_values = ['0.000', '0.000', '0', '0', 'False', '0']
        table_data = [
            ['参数', '当前值'],
            *[[lbl, val] for lbl, val in zip(self.status_labels, self.status_values)]
        ]
        self.table = self.ax3.table(cellText=table_data, cellLoc='center', loc='center',
                                    colWidths=[0.25, 0.25])
        self.table.auto_set_font_size(False)
        self.table.set_fontsize(10)
        self.table.scale(1, 1.8)

        plt.tight_layout()
        plt.show(block=False)

    def update_plot(self):
        """主线程调用：更新图表"""
        if not self.speech_probs:
            return

        x_data = list(range(len(self.speech_probs)))
        y_prob = list(self.speech_probs)
        y_vol = list(self.volume_rms_history)

        # ---- 语音概率图 ----
        self.prob_line.set_data(x_data, y_prob)
        for coll in list(self.ax1.collections):
            coll.remove()
        if self.speech_states:
            speech_mask = np.array(self.speech_states)
            if np.any(speech_mask):
                self.ax1.fill_between(x_data, 0, 1, where=speech_mask, alpha=0.3, color='green')

        current_threshold = 1.0 if self.event_is_talking.is_set() else SPEECH_THRESHOLD
        self.threshold_line.set_ydata([current_threshold, current_threshold])

        # ---- 音量图 ----
        self.vol_line.set_data(x_data[:len(y_vol)], y_vol)
        if len(x_data) > 0:
            self.ax2.set_xlim(max(0, len(x_data) - PLOT_HISTORY_SIZE), len(x_data))
            rms_max = max(max(y_vol, default=0), VOLUME_THRESHOLD + 0.01)
            high_vol = max(VOLUME_THRESHOLD + 0.01, rms_max * 1.3)
            self.ax2.set_ylim(-0.01, high_vol)

        # ---- 状态表格 ----
        current_prob = self.speech_probs[-1] if self.speech_probs else 0
        current_rms = self.volume_rms_history[-1] if self.volume_rms_history else 0

        new_vals = [
            f'{current_prob:.3f}',       # 对应行1：语音概率
            f'{current_rms:.4f}',        # 对应行2：RMS 音量
            str(self.speech_blocks),     # 对应行3：语音块数
            str(self.silence_blocks),    # 对应行4：静音块数
            str(self.is_speaking),       # 对应行5：是否说话
            str(len(self.audio_buffer)), # 对应行6：缓冲区大小
        ]

        # ✅ 修复：row_idx 从 1 到 6（共6行数据，第0行是表头）
        for row_idx in range(1, len(new_vals) + 1):
            cell = self.table[row_idx, 1]
            cell.get_text().set_text(new_vals[row_idx - 1])

            # 高亮逻辑（行号从1开始，第1行=语音概率，第2行=RMS，第5行=是否说话）
            if row_idx == 1 and current_prob > current_threshold:
                cell.set_facecolor('#FFCCCC')   # 语音概率高 → 红
            elif row_idx == 2 and current_rms < VOLUME_THRESHOLD:
                cell.set_facecolor('#FFCCCC')   # RMS 不够 → 红
            elif row_idx == 5 and self.is_speaking:
                cell.set_facecolor('#CCFFCC')   # 正在说话 → 绿
            else:
                cell.set_facecolor('white')

        self.fig.canvas.draw_idle()
        self.fig.canvas.flush_events()

    def callback(self, indata, frames, time, status):
        """音频回调（后台线程）"""
        if status:
            print(f"⚠️ 状态异常: {status}")
            return

        audio_chunk = indata[:, 0].copy()
        ring_buffer.extend(audio_chunk)

        # ---- VAD 推理 ----
        audio_tensor = torch.from_numpy(audio_chunk)
        speech_prob = model(audio_tensor, FS).item()

        # ✅ 新增：计算 RMS 音量
        rms = np.sqrt(np.mean(audio_chunk ** 2))

        # 存储可视化数据
        self.speech_probs.append(speech_prob)
        self.speech_states.append(self.is_speaking)
        self.volume_rms_history.append(rms)
        self.callback_count += 1

        if self.event_is_talking.is_set():
            vad_threshold = 1.0
            vol_ok = True          # 外部中断时不卡音量
        else:
            vad_threshold = SPEECH_THRESHOLD
            # ✅ 关键：音量必须大于阈值才认为是有效语音
            vol_ok = rms >= VOLUME_THRESHOLD

        # ✅ 综合判断：既要 VAD 认为在说话，又要音量够大
        if speech_prob > vad_threshold and vol_ok:
            self.speech_blocks += 1
            self.silence_blocks = 0
            if not self.is_speaking and self.speech_blocks >= SPEECH_BLOCKS_MIN:
                self.pipelineState.add_generation()
                print(f"🎤 检测到语音（概率={speech_prob:.2f}, RMS={rms:.4f}），开始录音...")
                self.is_speaking = True
                self.audio_buffer.extend(list(ring_buffer))
                ring_buffer.clear()
            if self.is_speaking:
                self.audio_buffer.extend(audio_chunk)
        else:
            self.silence_blocks += 1
            self.speech_blocks = 0
            if self.is_speaking:
                self.audio_buffer.extend(audio_chunk)
                if self.silence_blocks >= SILENCE_BLOCKS_MAX:
                    self.is_speaking = False
                    print("🛑 静音/低音量结束，录音完成")
                    if len(self.audio_buffer) > 0:
                        audio_np = np.array(self.audio_buffer, dtype=np.float32)
                        self.result_queue.put(audio_np)
                        self.audio_buffer.clear()
                        self.silence_blocks = 0

        # 标记需要更新图表
        if self.callback_count % PLOT_UPDATE_INTERVAL == 0:
            with self._update_lock:
                self._needs_update = True

    def auto_record(self):
        """主循环（主线程）"""
        try:
            while True:
                try:
                    audio_np = self.result_queue.get(timeout=0.1)
                except Empty:
                    with self._update_lock:
                        if self._needs_update:
                            self._needs_update = False
                            self.update_plot()
                    continue

                duration = len(audio_np) / FS
                if duration < MIN_SPEECH_DURATION:
                    print(f"⚠️ 录音 {duration:.1f}s 过短，跳过\n")
                    continue

                print(f"📝 录音时长: {duration:.1f}s")
                print("-" * 40 + "\n")
                self.update_plot()
                return audio_np

        except KeyboardInterrupt:
            print("\n👋 退出")
            self.stream.stop()
            self.stream.close()
            plt.close('all')

    def save_data(self, filename='vad_volume_debug.csv'):
        import csv
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Index', 'Prob', 'RMS', 'IsSpeaking', 'SpeechBlocks', 'SilenceBlocks'])
            for i in range(len(self.speech_probs)):
                writer.writerow([
                    i,
                    f'{self.speech_probs[i]:.3f}',
                    f'{self.volume_rms_history[i]:.4f}' if i < len(self.volume_rms_history) else '',
                    self.speech_states[i],
                    self.speech_blocks,
                    self.silence_blocks,
                ])
        print(f"📁 已保存: {filename}")


if __name__ == "__main__":
    event_is_talking = threading.Event()
    pipelineState = GenerationState()

    listener = AudioListener(pipelineState, event_is_talking)

    try:
        while True:
            audio = listener.auto_record()
            if audio is not None:
                print(f"收到录音: {len(audio)} 样本")
                # listener.save_data()
    except KeyboardInterrupt:
        print("\n结束")
        listener.stream.stop()
        listener.stream.close()
        plt.close('all')
