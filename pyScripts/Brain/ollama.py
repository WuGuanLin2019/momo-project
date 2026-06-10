import requests
import json

from Brain.conversation import conversation
from Core.State import GenerationState
from Utils.Timer import SmallTimer

TEXT_CUT = ["！", "。", "？", "，", "!", "："]


def judge_cut_text(s):
    for punct in TEXT_CUT:
        if punct in s:
            parts = s.split(punct)
            tail_str = None
            if len(parts) > 1:
                tail_str = parts[-1]

                pos =tail_str.find("”")
                if pos > -1:
                    tail_str = tail_str[pos + 1 :]
            return True, tail_str

    return False, None


def think(inputStr, callBack, myGen: GenerationState, pipeGen: GenerationState):
    with pipeGen.lock:
        myGen.generation = pipeGen.generation

    conversation.append({"role": "user", "content": inputStr})

    with SmallTimer("think"):
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                # qwen2.5:14b-instruct-q4_K_M
                # qwen2.5:3b-instruct-q4_K_M
                # gemma3:1b
                "model": "qwen2.5:14b-instruct-q4_K_M",
                "messages": conversation,
                "stream": True,
                "options": {
                    "num_predict": 128,
                    "repeat_penalty": 1.3,  # 2. 增大重复惩罚，防止无限循环
                    "temperature": 1,             # 3. 调整温度控制随机性
                    "top_k": 40,
                    "top_p": 0.9,
                },
            },
            stream=True,
        )

    conversation_cache = ""
    current_sentence = ""
    last_cut_str_tail = None
    for line in response.iter_lines():
        if not pipeGen.check_is_current_generation(myGen):
            return

        chunk = json.loads(line)
        isDone = chunk["done"]

        text = chunk["message"]["content"]
        if last_cut_str_tail is not None:
            text = last_cut_str_tail + text
            last_cut_str_tail = None

        is_cut, last_cut_str_tail = judge_cut_text(text)
        if is_cut and last_cut_str_tail is not None and last_cut_str_tail != "":
            text = text[: -len(last_cut_str_tail)]

        current_sentence += text
        conversation_cache += text

        if is_cut or isDone:
            callBack(current_sentence)
            print("【流式拼接】： " + current_sentence, end="\n", flush=True)

            current_sentence = ""

    if pipeGen.check_is_current_generation(myGen):
        conversation.append({"role": "assistant", "content": conversation_cache})


if __name__ == "__main__":
    think("介绍一下你自己")
