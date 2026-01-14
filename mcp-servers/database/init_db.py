import sqlite3
import os

db_path = r"c:/IIWII_DB/hndl-it/mcp-servers/database/main.db"
os.makedirs(os.path.dirname(db_path), exist_ok=True)

conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, content TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
c.execute("INSERT INTO notes (content) VALUES ('Welcome to your MCP Database')")
conn.commit()
conn.close()
print("Database created successfully.")
