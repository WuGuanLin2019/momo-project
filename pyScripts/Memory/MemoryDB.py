import datetime
import sqlite3
import uuid

class MemoryDB:
    def __init__(self, dbPath = "momo_memory.db"):
        self.conn = sqlite3.connect(dbPath)
        self.cursor = self.conn.cursor()

    def __init_table___(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS momo_memory(
            id TEXT,
            time TEXT,
            content TEXT,
            tags TEXT
        )
        """)
        self.conn.commit()

    def insert(self, content:str = "", tags:str = ""):
        uid = str(uuid.uuid4)
        now = datetime.now().isoformat()

        self.cursor.execute("""
        INSERT INFO momo_memory(id,time,content,tags)
        VALUES(?,?,?,?)
        """,(uid,now,content,tags))
        self.conn.commit()
        return uid

    def searchByTags(self,tags:str):
        self.cursor.execute("""
        SELECT * FORM momo_memory
        WHERE LIKE ?
        """,(f"%{tags}%"))
        return self.cursor.fetchall()
    