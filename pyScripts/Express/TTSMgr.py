# from .Kokoro import text_to_audioData
# from Express.Moss import tts_synthesize
from Express.TTS_Client import request_audio_data


import re
import emoji

def clean_text_for_tts(text):
    # --- 第一层：移除所有Markdown/格式符号 ---
    # 移除加粗 **文本**
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    # 移除斜体 *文本*（避免误伤，只处理成对出现的）
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    # 移除标题 # ## ###
    text = re.sub(r'#{1,6}\s*', '', text)
    # 移除引用符号 >
    text = re.sub(r'>\s*', '', text)
    
    # --- 第二层：移除所有Emoji和特殊符号 ---
    # 移除所有emoji
    text = emoji.replace_emoji(text, replace='')
    # 移除常见装饰符号（如✨💭🔮📐）
    text = re.sub(r'[✨💭🔮📐🧠⚡🌅💖]', '', text)
    # 移除带圈数字和序号（① ② ③ / 1️⃣ 2️⃣）
    text = re.sub(r'[①②③④⑤⑥⑦⑧⑨⑩]', '', text)
    text = re.sub(r'[0-9]️⃣', '', text)
    
    # --- 第三层：移除括号内的“舞台提示”和“动作描述” ---
    # 移除（像这样的内容）
    text = re.sub(r'[（(][^）)]*[）)]', '', text)
    # 移除【这样的标签】
    text = re.sub(r'【[^】]*】', '', text)
    # 移除 [] 内的描述（如 [笑声]）
    text = re.sub(r'\[[^\]]*\]', '', text)
    
    # --- 第四层：处理标点和连接词，让语音更自然 ---
    text = re.sub(r'\n{2,}', '。', text)  # 多个换行→句号
    
    # --- 第五层：清理空白和杂项 ---
    text = re.sub(r'\s+', ' ', text)   # 多个空格→一个
    text = text.strip()
    
    return text

def ttsData(text) :
    clear_str = clean_text_for_tts(text)
    if not clear_str:
        return
    return request_audio_data(clear_str)