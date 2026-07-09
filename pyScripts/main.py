import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"   # <-- 添加这一行，必须在所有 import 之前


import time
from Core.Pipeline import AssistantPipeline
import sys


mainP = AssistantPipeline()
mainP.start()

print("Assistant running... 按 Ctrl+C 退出")

try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    # mainP.shut_down()
    print("\n用户手动退出，程序结束")
    
    sys.exit(0)