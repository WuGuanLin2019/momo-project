from enum import Enum
from Memory.MemoryMgr import memory_mgr
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
        fun(dataStr)


class KeyWordHandler:
    def __init__(self, pattern) -> None:
        self.pattern = pattern

    def fun(self, inputStr: str):
        # 注意这里去掉了空格，那么pattern里也不能有空格！
        result = re.findall(self.pattern, inputStr.strip())
        return result


def note_memory(mStr: str)->bool:
    """
    有要记下的东西的时去调用

    Args:
        mStr (str): 要记忆的字符串,尽量控制在30字内

    Returns:
        bool:是否成功执行
    """
    result = memory_mgr.note(mStr)
    return result


def remind(searchKey: str) -> str:
    """
    在你需要回忆，或者当信息不足时使用"

    Args:
        mStr (str): 和记忆相关的查询关键字,尽量控制在30字内

    Returns:
        str:查询到的记忆字符串
    """
    result = memory_mgr.remind(searchKey)
    return result


Tools = [note_memory, remind]
ToolsMap = {func.__name__: func for func in Tools}

def call_tool(tool_calls):
    results = []
    for call in tool_calls:
        fun_name = call.function.name
        tool = ToolsMap.get(fun_name, False)
        if not tool:
            print("没找到对应tool：" + fun_name)
            return None

        try:
            result = tool(**call.function.arguments)
            results.append(result)
        except Exception as e:
            print(f"执行工具 {fun_name} 时出错: {e}")
            results.append(None)   # 或者将异常信息放入结果

    return results
