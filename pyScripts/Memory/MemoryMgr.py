from Memory.MemoryDB import MemoryDB


class MemoryMgr:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self.db = MemoryDB()

    def note(self, mStr: str):
        if not mStr:
            return False

        print(f"【记住记忆】{mStr}")
        try:
            self.db.insert(mStr)
        except Exception as e:
            print(f"记忆数据库插入失败{e}")
            return False

        return True

    def remind(self, kStr):
        if not kStr or len(kStr) < 1:
            return
        print(f"【读取记忆】{kStr}")
        memory_data = ""
        try:
            memory_data = self.db.searchByTags(kStr)
        except Exception as e:
            print(f"记忆数据库搜索错误{e}")
            return False
        return memory_data


memory_mgr = MemoryMgr()
