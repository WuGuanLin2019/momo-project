
from fastapi import FastAPI
import uvicorn
from funasr import AutoModel
from pydantic import BaseModel
from numpy.typing import NDArray
import numpy as np
from fastapi.responses import JSONResponse, Response

BACKEND_PORT = 5003

chunk_size = [10, 10, 5] #[0, 10, 5] 600ms, [0, 8, 4] 480ms
encoder_chunk_look_back = 4 #number of chunks to lookback for encoder self-attention
decoder_chunk_look_back = 1 #number of encoder chunks to lookback for decoder cross-attention

class Request(BaseModel):
    audio_buffer :list[float]
    is_done: bool = False


class FunasrAudioToText:
    def __init__(self):
        self.cache_data = {}
        self.model = AutoModel(
            model="iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-online",
        )

    def clear_cache(self):
        print(f"[FunasrAudioToText] clear_cache")
        self.cache_data = {}

    def stream_audio_to_text(self, data, is_done: bool):
        is_interage = False
        if is_interage:
            self.clear_cache()
            return "", False

        if not isinstance(data, np.ndarray):
            data = np.array(data, dtype=np.float32)

        print(f"data size:{data.size}")
        res = self.model.generate(
            input=data,
            cache=self.cache_data,
            is_final=is_done,
            chunk_size = chunk_size,
            encoder_chunk_look_back = encoder_chunk_look_back,
            decoder_chunk_look_back = decoder_chunk_look_back,
        )

        print(f"is_done:{is_done}")
        if is_done:
            self.clear_cache()


        print(f"[FunasrAudioToText] res:{res}")
        return res[0]["text"], is_done


FunasrAudioToTexter = FunasrAudioToText()
app = FastAPI()

@app.post("/stt/fun")
async def stt(request: Request):
    txt,is_done = FunasrAudioToTexter.stream_audio_to_text(request.audio_buffer, request.is_done)
    return JSONResponse([txt,is_done])
    # return Response(content=[txt,is_done])

@app.post("/stt/interage")
async def interage():
    FunasrAudioToTexter.clear_cache()


if __name__ == "__main__":
    print(f"[main] 启动 uvicorn: http://127.0.0.1:{BACKEND_PORT}", flush=True)
    uvicorn.run(app, host="127.0.0.1", port=BACKEND_PORT)
