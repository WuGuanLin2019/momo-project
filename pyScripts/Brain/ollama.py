from Brain.conversation import conversation
from Brain.SentenceHandler import SentenceHandler
from Core.Action import Tools, call_tool
from Core.State import GenerationState
from Utils.Timer import SmallTimer
from ollama import chat 

def when_think_end(sh:SentenceHandler,add_to_input_queue):
    print("Brain end")
    conversation.append(
        {
            "role": "assistant",
            "content": sh.content,
            "tool_calls": sh.tool_calls,
        }
    )

    #调用工具
    if sh.tool_calls:
        try:
            results = call_tool(sh.tool_calls)
            handle_results(results,add_to_input_queue)
        except Exception as e:
            print(f"call_tool error:{e}")

def handle_results(results,add_to_input_queue):
    for k,v in results.items():
        print(k,v)
        add_to_input_queue(v)
        # if k == "remind" or k == "note_memory":
        #     add_to_input_queue(v)

        
def think(inputStr, add_to_speak_queue,add_to_input_queue, myGen: GenerationState, pipeGen: GenerationState):
    with pipeGen.lock:
        myGen.generation = pipeGen.generation

    conversation.append({"role": "user", "content": inputStr})

    stream = chat(
        # gemma3:1b
        # qwen2.5:3b-instruct-q4_K_M
        # llama3.1
        # qwen2.5:14b-instruct-q4_K_M
        # deepseek-r1:8b
        # qwen3.5:9b
        model="qwen3.5:9b",
        messages=conversation,
        tools=Tools,
        stream=True,
        think = False,
        options={
            # "num_predict": 256,
            "repeat_penalty": 1.3,
            "temperature": 0.5,
            "top_k": 40,
            "top_p": 0.9,
        },
        
    )

    sentenceHandler = SentenceHandler()

    try:
        for chunk in stream:
            if not pipeGen.check_is_current_generation(myGen):
                when_think_end(sentenceHandler,add_to_input_queue)
                break

            currentSteamingText = sentenceHandler.handleStreamingText(chunk)
            if currentSteamingText:
                add_to_speak_queue(currentSteamingText)
    except Exception as e:
        print(f"stream error:{e}")

    if pipeGen.check_is_current_generation(myGen):
        when_think_end(sentenceHandler,add_to_input_queue)


# if __name__ == "__main__":
#     think("介绍一下你自己")
