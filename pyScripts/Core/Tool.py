import queue

def clearQueue(q):
    try:
        while True:
            q.get_nowait()
    except queue.Empty:
        pass