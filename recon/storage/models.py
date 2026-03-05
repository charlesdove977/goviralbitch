"""
Data models for assets and collections with CRUD operations.
Ported from ReelRecon — unchanged logic, imports adjusted.
"""

import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from .database import get_db_connection, db_transaction


@dataclass
class Asset:
    """Represents a saved asset (reports or granular items)."""
    id: str
    type: str
    title: Optional[str] = None
    content_path: Optional[str] = None
    preview: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    starred: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def create(cls, type: str, title: str, content_path: str = None,
               preview: str = None, metadata: dict = None) -> 'Asset':
        asset = cls(
            id=str(uuid.uuid4()), type=type, title=title,
            content_path=content_path, preview=preview, metadata=metadata,
            starred=False,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        with db_transaction() as conn:
            conn.execute(
                "INSERT INTO assets (id, type, title, content_path, preview, metadata, starred, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (asset.id, asset.type, asset.title, asset.content_path,
                 asset.preview, json.dumps(asset.metadata) if asset.metadata else None,
                 int(asset.starred), asset.created_at, asset.updated_at)
            )
        return asset

    @classmethod
    def get(cls, asset_id: str) -> Optional['Asset']:
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        conn.close()
        return cls._from_row(row) if row else None

    @classmethod
    def list(cls, type: str = None, starred: bool = None,
             collection_id: str = None, limit: int = 50, offset: int = 0) -> List['Asset']:
        conn = get_db_connection()
        query = "SELECT DISTINCT a.* FROM assets a"
        params = []
        conditions = []
        if collection_id:
            query += " JOIN asset_collections ac ON a.id = ac.asset_id"
            conditions.append("ac.collection_id = ?")
            params.append(collection_id)
        if type:
            conditions.append("a.type = ?")
            params.append(type)
        if starred is not None:
            conditions.append("a.starred = ?")
            params.append(int(starred))
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY a.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [cls._from_row(row) for row in rows]

    @classmethod
    def search(cls, query: str, limit: int = 20) -> List['Asset']:
        conn = get_db_connection()
        rows = conn.execute(
            "SELECT a.* FROM assets a JOIN assets_fts fts ON a.rowid = fts.rowid WHERE assets_fts MATCH ? ORDER BY rank LIMIT ?",
            (query, limit)
        ).fetchall()
        conn.close()
        return [cls._from_row(row) for row in rows]

    def update(self, **kwargs) -> 'Asset':
        allowed = {'title', 'content_path', 'preview', 'metadata', 'starred'}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return self
        for key, value in updates.items():
            setattr(self, key, value)
        self.updated_at = datetime.utcnow().isoformat()
        with db_transaction() as conn:
            set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
            values = []
            for k, v in updates.items():
                if k == 'metadata':
                    values.append(json.dumps(v) if v else None)
                elif k == 'starred':
                    values.append(int(v))
                else:
                    values.append(v)
            values.append(self.updated_at)
            values.append(self.id)
            conn.execute(f"UPDATE assets SET {set_clause}, updated_at = ? WHERE id = ?", values)
        return self

    def delete(self):
        with db_transaction() as conn:
            conn.execute("DELETE FROM assets WHERE id = ?", (self.id,))

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id, 'type': self.type, 'title': self.title,
            'content_path': self.content_path, 'preview': self.preview,
            'metadata': self.metadata, 'starred': self.starred,
            'created_at': self.created_at, 'updated_at': self.updated_at
        }

    @classmethod
    def _from_row(cls, row) -> 'Asset':
        return cls(
            id=row['id'], type=row['type'], title=row['title'],
            content_path=row['content_path'], preview=row['preview'],
            metadata=json.loads(row['metadata']) if row['metadata'] else None,
            starred=bool(row['starred']),
            created_at=row['created_at'], updated_at=row['updated_at']
        )


@dataclass
class Collection:
    """Represents a user-defined collection/group of assets."""
    id: str
    name: str
    description: Optional[str] = None
    color: str = '#6366f1'
    icon: Optional[str] = None
    created_at: Optional[str] = None

    @classmethod
    def create(cls, name: str, description: str = None,
               color: str = '#6366f1', icon: str = None) -> 'Collection':
        collection = cls(
            id=str(uuid.uuid4()), name=name, description=description,
            color=color, icon=icon, created_at=datetime.utcnow().isoformat()
        )
        with db_transaction() as conn:
            conn.execute(
                "INSERT INTO collections (id, name, description, color, icon, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (collection.id, collection.name, collection.description,
                 collection.color, collection.icon, collection.created_at)
            )
        return collection

    @classmethod
    def list(cls) -> List['Collection']:
        conn = get_db_connection()
        rows = conn.execute("SELECT * FROM collections ORDER BY name").fetchall()
        conn.close()
        return [cls._from_row(row) for row in rows]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id, 'name': self.name, 'description': self.description,
            'color': self.color, 'icon': self.icon, 'created_at': self.created_at
        }

    @classmethod
    def _from_row(cls, row) -> 'Collection':
        return cls(
            id=row['id'], name=row['name'], description=row['description'],
            color=row['color'], icon=row['icon'], created_at=row['created_at']
        )


class AssetCollection:
    @staticmethod
    def add(asset_id: str, collection_id: str):
        with db_transaction() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO asset_collections (asset_id, collection_id, added_at) VALUES (?, ?, ?)",
                (asset_id, collection_id, datetime.utcnow().isoformat())
            )

    @staticmethod
    def remove(asset_id: str, collection_id: str):
        with db_transaction() as conn:
            conn.execute(
                "DELETE FROM asset_collections WHERE asset_id = ? AND collection_id = ?",
                (asset_id, collection_id)
            )
