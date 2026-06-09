import queue
from Core.State import GenerationState
from Core.Tool import clearQueue
from Listener.Faster_Whisper import audio_to_text
from Listener.SileroVAD import AudioListener


def loop(input_text_queue: queue.Queue, pipelineState: GenerationState):
    audioListener = AudioListener(pipelineState)
    generate_state = GenerationState()
    def check_generate_break():
        return not pipelineState.check_is_current_generation(generate_state)

    while True:
        audio_float = audioListener.auto_record()
        pipelineState.update_newest_generation(generate_state)
        
        audio_str = audio_to_text(audio_float)

        if check_generate_break():
            clearQueue(input_text_queue)
            continue
        input_text_queue.put(audio_str)

