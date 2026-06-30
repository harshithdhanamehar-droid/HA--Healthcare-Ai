"""
DB migration: add missing columns to users table.
Safe to run multiple times — checks column existence before ALTER.
"""
import sqlite3, sys

DB = "ha_healthcare.db"
conn = sqlite3.connect(DB)
cur  = conn.cursor()

def has_col(table, col):
    cur.execute(f"PRAGMA table_info({table})")
    return any(r[1] == col for r in cur.fetchall())

migrations = [
    ("users", "email",         "ALTER TABLE users ADD COLUMN email TEXT"),
    ("users", "password_hash", "ALTER TABLE users ADD COLUMN password_hash TEXT"),
    ("users", "auth_provider", "ALTER TABLE users ADD COLUMN auth_provider TEXT DEFAULT 'local'"),
    ("users", "google_sub",    "ALTER TABLE users ADD COLUMN google_sub TEXT"),
    ("users", "is_verified",   "ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 0"),
    ("users", "updated_at",    "ALTER TABLE users ADD COLUMN updated_at TEXT"),
]

for table, col, sql in migrations:
    if not has_col(table, col):
        cur.execute(sql)
        print(f"  + added {table}.{col}")
    else:
        print(f"  ✓ {table}.{col} already exists")

# Backfill updated_at where NULL
cur.execute("UPDATE users SET updated_at = created_at WHERE updated_at IS NULL")

# Create unique index on email (if not exists)
cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)")
cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_sub ON users(google_sub)")

conn.commit()
conn.close()
print("Migration complete.")
