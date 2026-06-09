from kokoro import KPipeline
import soundfile as sf
import sounddevice as sd

print("加载Kokoro...")

pipeline = KPipeline(
	lang_code='z',
 	repo_id= "hexgrad/Kokoro-82M"
)

text = "你爱或者不爱我，爱就在那里，不悲不喜。"

# 这里在调用时指定 voice
generator = pipeline(text, voice='zf_xiaobei')

for i, (gs, ps, audio) in enumerate(generator):
    sf.write("output.wav", audio, 24000)
    print("生成完成")
    break

# 播放
data, sr = sf.read("output.wav")
sd.play(data, sr)
sd.wait()
print("播放完成")