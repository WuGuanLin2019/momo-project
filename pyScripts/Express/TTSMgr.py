class TTSQueuer:
    audio2text_queue = []

    def AddSpeakStr(this, str):
        this.audio2text_queue.append(str)

    def ClearSpeakQueue(this):
        this.audio2text_queue.clear()

    def Loop(this):
        pass