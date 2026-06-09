import requests
import whisper

model = whisper.load_model("tiny")
print("开始识别...")
result = model.transcribe("../test_介绍一下自己吧.m4a", language="zh")

print(result["text"])
prompt = result["text"]

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "gemma3:1b",
        "prompt": prompt,
        "stream": False
    }
)

print(response.json()["response"])