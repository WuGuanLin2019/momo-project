import whisper

print("加载模型...")

model = whisper.load_model("tiny")

print("开始识别...")

result = model.transcribe("test_介绍一下自己吧.m4a", language="zh")

print(result["text"])