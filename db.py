import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'data' / 'acmon.db'


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS kv (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    ''')
    conn.commit()
    conn.close()


def get_all():
    conn = get_db()
    rows = conn.execute('SELECT key, value FROM kv').fetchall()
    conn.close()
    return {row['key']: json.loads(row['value']) for row in rows}


def set_kv(key, value):
    conn = get_db()
    conn.execute(
        "INSERT INTO kv (key, value, updated_at) VALUES (?, ?, datetime('now')) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at",
        (key, json.dumps(value))
    )
    conn.commit()
    conn.close()


def delete_kv(key):
    conn = get_db()
    conn.execute('DELETE FROM kv WHERE key = ?', (key,))
    conn.commit()
    conn.close()


def export_all():
    return get_all()


def import_all(data):
    conn = get_db()
    conn.execute('DELETE FROM kv')
    for key, value in data.items():
        conn.execute(
            "INSERT INTO kv (key, value, updated_at) VALUES (?, ?, datetime('now'))",
            (key, json.dumps(value))
        )
    conn.commit()
    conn.close()
