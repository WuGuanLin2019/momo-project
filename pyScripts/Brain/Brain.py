from Brain.ollama import think
from Core.State import GenerationState, SpeakTask


def loop(input_text_queue, to_speak_queue, pipelineState: GenerationState):
    generate_state = GenerationState()

    def add_to_queue(str):
        if str.strip() != "":
            task = SpeakTask(generate_state.generation,str)
            to_speak_queue.put(task)

    while True:
        inputStr = input_text_queue.get()
        pipelineState.update_newest_generation(generate_state)


        if not pipelineState.check_is_current_generation(generate_state):
            continue
        think(inputStr, add_to_queue, generate_state, pipelineState)
