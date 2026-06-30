import datetime
import sqlite3
import time
from ollama import embeddings
from dataclasses import dataclass, field

from Data.config import DB_PATH


@dataclass
class MemoryData:
    content: str = ""
    summary: list[str] = field(default_factory=list)
    actors: list[str] = field(default_factory=list)
    objects: list[str] = field(default_factory=list)
    emotions: list[str] = field(default_factory=list)
    environment: list[str] = field(default_factory=list)


def cal_embedding(input: str):
    print(f"开始计算embedding：{input}")
    res = embeddings(model="nomic-embed-text", prompt=input)

    vector = res["embedding"]
    return vector


class MemoryDB:
    def __init__(self, dbPath):
        self.conn = sqlite3.connect(dbPath, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.embeddingDic = {}
        self.__init_table__()

    def __init_table__(self):
        self.cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS momo_memory(
            uid INTEGER,
            time TEXT,
            content TEXT,
            summary TEXT
        )
        """
        )
        # 建 B-Tree 索引，加速 uid 精确查询
        self.cursor.execute(
            """
        CREATE INDEX IF NOT EXISTS idx_uid ON momo_memory(uid)
        """
        )
        self.conn.commit()


    def insert(self, mData:MemoryData):
        uid = int(time.time() * 1_000_000)
        # mid = self.__getMId()
        now = datetime.datetime.now().isoformat()
        content = mData.content
        summary = ",".join(mData.summary)

        self.cursor.execute(
            """
        INSERT INTO momo_memory(uid,time,content,summary)
        VALUES(?,?,?,?)
        """,
            (uid, now, content, summary),
        )
        self.conn.commit()
        return uid

    def rewrite(self,uid:int,mData:MemoryData):
        content = mData.content
        summary = ",".join(mData.summary)
        self.cursor.execute(
            """
        UPDATE momo_memory
        SET content=?,summary=?
        WHERE uid=?
        """,
            (content, summary, uid),
        )
        self.conn.commit()

    def searchByUids(self, uids: list[int]):
        if not uids:
            return None
        placeholders = ",".join("?" * len(uids))
        self.cursor.execute(
            f"""
        SELECT * FROM momo_memory
        WHERE uid IN ({placeholders})
        """,
            uids,
        )
        return self.cursor.fetchall()
