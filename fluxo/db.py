"""Banco local (SQLite). Estado de cada contato, envios e descadastros."""
import sqlite3
from contextlib import contextmanager

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    place_id TEXT UNIQUE,
    name TEXT NOT NULL,
    address TEXT,
    phone TEXT,
    email TEXT,
    rating REAL,
    rating_count INTEGER,
    status TEXT NOT NULL DEFAULT 'novo',   -- novo | contatado | respondeu | interessado | recusou | descadastrado
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS sends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER NOT NULL REFERENCES contacts(id),
    channel TEXT NOT NULL,                  -- email
    subject TEXT,
    dry_run INTEGER NOT NULL,
    provider_id TEXT,
    sent_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS replies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id INTEGER NOT NULL REFERENCES contacts(id),
    body TEXT NOT NULL,
    classification TEXT,
    received_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS unsubscribes (
    email TEXT PRIMARY KEY,
    created_at TEXT DEFAULT (datetime('now'))
);
"""


@contextmanager
def connect(path=None):
    conn = sqlite3.connect(path or config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
