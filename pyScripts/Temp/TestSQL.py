import sqlite3

con = sqlite3.connect("memory.db")
cursor = con.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS memory(
        id TEXT,
        content TEXT,
        time TEXT
    )
""")

con.commit()

cursor.execute("""
INSERT INTO memory (id, content, time)
VALUES (?, ?, ?)
""", ("1", "Wu吃了苹果", "2026-01-03 17:43"))

con.commit()

cursor.execute("SELECT * FROM memory")
print(cursor.fetchall())

cursor.execute("""
SELECT * FROM memory
WHERE content LIKE '%苹果%'
""")

print(cursor.fetchall())