from enum import Enum
from Memory.MemoryDB import MemoryData
from Memory.MemoryMgr import RecallData, memory_mgr
import re


class ActionType(Enum):
    Memory = 1


ACTION_CONFIG = {
    ActionType.Memory: {
        "note": {"fun": memory_mgr.note, "pattern": r"【记住记忆：(.+?)】"},
        "remind": {"fun": memory_mgr.remind, "pattern": r"【获取记忆：(.+?)】"},
    }
}


class Action:
    def __init__(self, actionType: ActionType):
        self.actionType = actionType

    def start(self, subActionType: str, inputStr: str):
        if not inputStr:
            return
        if self.actionType not in ACTION_CONFIG:
            print(f"未配置 action: {self.actionType.name}")
            return

        action = ACTION_CONFIG[self.actionType]

        if subActionType not in action:
            print(f"未配置action fun: {subActionType}")
            return
        subAction = action[subActionType]

        pattern = subAction.get("pattern")
        fun = subAction.get("fun")
        if not pattern:
            print(f"未配置subaction pattern: {subActionType}")
            return
        if not fun:
            print(f"未配置subaction fun: {subActionType}")
            return

        kh = KeyWordHandler(pattern)
        dataStr = kh.fun(inputStr)
        # fun(dataStr)


class KeyWordHandler:
    def __init__(self, pattern) -> None:
        self.pattern = pattern

    def fun(self, inputStr: str):
        # 注意这里去掉了空格，那么pattern里也不能有空格！
        result = re.findall(self.pattern, inputStr.strip())
        return result


def note_memory(content: str, summary: list[str]) -> str:
    """
    有要记下的东西的时去调用，以下事情你可以主动去记下：
    一些你作为AI“自我”的信息，比如名称，兴趣，爱好，状态信息等；
    关于你创造者Wu的信息，比如名称，兴趣，爱好，性格，状态信息等；
    一些你与Wu互动的信息，比如你与Wu的对话，互动，互动的场景等；

    Args:
        content (str): 完整的事实描述，保留核心信息（时间、人物、事件、结果），不超过50字。
        summary (list[str]): 多角度概要短语(建议按核心事件，物体，角色，情绪，场景去拆分)，每个元素不超过10字，用于向量检索。



    示例：

    当你听到：今天我度过了难忘的一天，今天在家里吃苹果很开心
    调用：
        note_memory(
            content="用户在家里吃苹果，很开心。",
            summary=["在家吃苹果", "苹果","用户（Wu）","心情愉悦","家里"],
        )
    """

    # print(f"content:{content}\nsummary{summary}\n events{events}\nobject{object}\n emotion{emotion}\n environment{environment}")
    # data = MemoryData(content,summary,actors,objects=objects,emotions=emotions,environment=environment)
    data = MemoryData()
    data.content = content
    data.summary = summary

    result = False
    result = memory_mgr.note(data)
    if result:
        return "已成功记下记忆"
    else:
        return "记忆失败，你没能记住记忆"


def remind(searchKey: list[str]) -> str:
    """
    在你需要回忆，或者当信息不足时使用

    Args:
        mStr (str): 搜索关键词，必须是简短的关键词组合，如"用户给AI起的名字"，不超过15字

    Returns:
        str:查询到的记忆字符串

    示例：

    当你想知道你的名字时
    调用：
        remind(
            searchKey=["AI", "名字"],
        )

    """
    results: list[RecallData]|None = memory_mgr.remind(searchKey)
    result_strs = []
    idx = 1
    if not results:
        return "没有找到相关记忆"
    for cur in results:
        mid = cur.mid
        timeStr = cur.timeStr
        content = cur.content
        resultStr =f"mid：{mid}。保存时间：{timeStr}。记忆片段：{content}" 
        result_strs.append(resultStr)
        idx += 1
    return "\n".join(result_strs)


def change_thought(mid:str, content: str, summary: list[str]) -> str:
    """
    当发现与之前记忆不一致时，可以修改记忆。
    一次只能修改一条，如需修改多条请多次调用。

    Args:
        mid (str): 最相关的记忆的唯一id（必须是一个ID，不能是多个）。
        content (str): 完整的事实描述，保留核心信息（时间、人物、事件、结果），不超过50字。
        summary (list[str]): 多角度概要短语(建议按核心事件，物体，角色，情绪，场景去拆分)，每个元素不超过10字，用于向量检索。

    示例：

    当你听到Wu说：给你重新改个名字，叫MOMO。
    然后你发现和之前的记忆“mid:xxx。记忆我的名字叫JOJO”相冲突时，
    调用：
        change_thought(
            mid = "xxx",
            content="WU重新为我取名为MOMO",
            summary=["改名", "MOMO","用户（Wu）"],
        )
    """
    mData = MemoryData()
    mData.content = content
    mData.summary = summary
    result = memory_mgr.rewrite(mid, mData)
    if result:
        return "已成功修改记忆"
    else:
        return "重写记忆失败"


Tools = [note_memory, remind, change_thought]
ToolsMap = {func.__name__: func for func in Tools}

def call_tool(tool_calls):
    if not tool_calls:
        return
    results = {}
    for call in tool_calls:
        fun_name = call.function.name
        tool = ToolsMap.get(fun_name)
        if not tool:
            print("没找到对应tool：" + fun_name)
            continue

        try:
            result = tool(**call.function.arguments)
            results[fun_name] = result
        except Exception as e:
            print(f"执行函数 {fun_name} 时出错: {e}")
            results[fun_name] = "error"

    return results
