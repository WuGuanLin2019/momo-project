import time

class SmallTimer:
    def __init__(this, title:str):
        this.title = title

    def __enter__(this):
        this.beginT =  time.perf_counter()

    def __exit__(this,*args):
        this.endT =  time.perf_counter()
        print(f"【 { this.title } 】 耗时：{ this.endT - this.beginT:.2f}s")

