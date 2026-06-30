import sqlite3
conn = sqlite3.connect(r'ha_healthcare.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print('Tables:', tables)
for t in tables:
    cursor.execute(f'PRAGMA table_info({t})')
    cols = [(r[1], r[2]) for r in cursor.fetchall()]
    print(f'  {t}: {[c[0] for c in cols]}')
conn.close()
