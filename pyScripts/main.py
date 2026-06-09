import time
from Core.Pipeline import AssistantPipeline


mainP = AssistantPipeline()
mainP.start()

print("Assistant running... 按 Ctrl+C 退出")

try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    # mainP.shut_down()
    print("\n用户手动退出，程序结束")