import sqlite3
from flask import g, current_app
import os

def get_db():
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    db = get_db()
    cur = db.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    return cur.lastrowid

def get_next_pk(entity_name: str) -> int:
    """Generates the next Z_PK for a given Core Data entity and updates Z_PRIMARYKEY."""
    db = get_db()
    cur = db.execute("SELECT Z_ENT, Z_MAX FROM Z_PRIMARYKEY WHERE Z_NAME = ? OR Z_NAME = ?;", (entity_name, f"Z{entity_name.upper()}"))
    row = cur.fetchone()
    
    if not row:
        # Fallback: find entity_name in Z_NAME case-insensitively
        cur = db.execute("SELECT Z_ENT, Z_MAX FROM Z_PRIMARYKEY WHERE LOWER(Z_NAME) = LOWER(?);", (entity_name,))
        row = cur.fetchone()
        
    if row:
        ent_id = row['Z_ENT']
        current_max = row['Z_MAX']
        new_pk = current_max + 1
        db.execute("UPDATE Z_PRIMARYKEY SET Z_MAX = ? WHERE Z_ENT = ?;", (new_pk, ent_id))
        db.commit()
        return new_pk
    else:
        # If not tracked in Z_PRIMARYKEY, query MAX(Z_PK) from target table
        table_name = f"Z{entity_name.upper()}" if not entity_name.startswith("Z") else entity_name
        cur = db.execute(f"SELECT MAX(Z_PK) as max_pk FROM '{table_name}';")
        row = cur.fetchone()
        max_pk = row['max_pk'] if row and row['max_pk'] else 0
        return max_pk + 1
