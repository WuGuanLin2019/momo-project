from Core.State import GenerationState
import queue
from Core.State import GenerationState
from Utils.Tool import clearQueue
from Listener.Faster_Whisper import audio_to_text
from Listener.SileroVAD import AudioBufferData, AudioListener, AudioStreamListener
from Listener.STT_Client import STT_Loop,  request_audio_text
import threading



def listen_loop(input_text_queue: queue.Queue, pipelineState: GenerationState,  event_is_talking):
    audioListener = AudioStreamListener(pipelineState,event_is_talking)
    my_generate_state: GenerationState = GenerationState()
    def check_generate_break():
        return not pipelineState.check_is_current_generation(my_generate_state)

    abDatas = queue.Queue()
    stt_thread = threading.Thread(
        target=STT_Loop, args=(abDatas,input_text_queue,check_generate_break)
    ).start()

    while True:
        try:
            abData:AudioBufferData|None = audioListener.auto_record()
            if abData is None:
                continue
        except Exception as e:
            print(f"音频录制异常:{e}")
            continue

        pipelineState.update_newest_generation(my_generate_state)
        abDatas.put(abData)


        # audio_str,is_done = request_audio_text(abData)

        # if not is_done or not audio_str:
        #     continue

        # if check_generate_break():
        #     clearQueue(input_text_queue)
        #     interage_audio_text()
        #     continue

        # input_text_queue.put(audio_str)

