import torch
import ChatTTS
from IPython.display import Audio  # 如果在 Jupyter，或者直接保存 wav

# 初始化
chat = ChatTTS.Chat()
chat.load(compile=False)  # 首次会下载模型，指定你的缓存路径

# 固定一个音色种子（抽到喜欢的就记下来）
spk_seed = 2222
torch.manual_seed(spk_seed)

# 准备你要说的文本，直接中英混写
texts = [
    "大家好，欢迎来到我的直播间，今天我们来玩点刺激的。",
    "哇，这波操作真的是太帅了，简直就是 ACE 啊！",
    "等一下，我先喝口水，这个 boss 有点难搞。",
]

# 合成
wavs = chat.infer(texts, use_decoder=True)

# 保存第一段音频
import soundfile as sf
sf.write('output.wav', wavs[0], 24000)