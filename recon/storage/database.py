"""
SQLite database initialization and connection management.
DB stored at data/recon/recon.db (adjusted from ReelRecon).
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager

DATABASE_PATH = Path(__file__).parent.parent.parent / 'data' / 'recon' / 'recon.db'

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS assets (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    title TEXT,
    content_path TEXT,
    preview TEXT,
    metadata JSON,
    starred INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS collections (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    color TEXT DEFAULT '#6366f1',
    icon TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS asset_collections (
    asset_id TEXT,
    collection_id TEXT,
    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (asset_id, collection_id),
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
    FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE
);

CREATE VIRTUAL TABLE IF NOT EXISTS assets_fts USING fts5(
    title,
    preview,
    content='assets',
    content_rowid='rowid'
);

CREATE TRIGGER IF NOT EXISTS assets_ai AFTER INSERT ON assets BEGIN
    INSERT INTO assets_fts(rowid, title, preview)
    VALUES (NEW.rowid, NEW.title, NEW.preview);
END;

CREATE TRIGGER IF NOT EXISTS assets_ad AFTER DELETE ON assets BEGIN
    INSERT INTO assets_fts(assets_fts, rowid, title, preview)
    VALUES ('delete', OLD.rowid, OLD.title, OLD.preview);
END;

CREATE TRIGGER IF NOT EXISTS assets_au AFTER UPDATE ON assets BEGIN
    INSERT INTO assets_fts(assets_fts, rowid, title, preview)
    VALUES ('delete', OLD.rowid, OLD.title, OLD.preview);
    INSERT INTO assets_fts(rowid, title, preview)
    VALUES (NEW.rowid, NEW.title, NEW.preview);
END;

CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(type);
CREATE INDEX IF NOT EXISTS idx_assets_starred ON assets(starred);
CREATE INDEX IF NOT EXISTS idx_assets_created_at ON assets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_asset_collections_asset ON asset_collections(asset_id);
CREATE INDEX IF NOT EXISTS idx_asset_collections_collection ON asset_collections(collection_id);
"""


def init_db():
    """Initialize the database with schema. Safe to call multiple times."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()
    return DATABASE_PATH


def get_db_connection():
    """Get a database connection with row factory enabled."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_transaction():
    """Context manager for database transactions."""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
