"""
database.py — SQLite database layer for Thesis Resource Manager.
Handles schema creation and all CRUD operations.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "thesis_manager.db")


def get_connection():
    """Return a connection to the SQLite database with row-factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS theses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            file_path   TEXT,
            file_type   TEXT,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS categories (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT NOT NULL UNIQUE,
            color TEXT NOT NULL DEFAULT '#3B82F6'
        );

        CREATE TABLE IF NOT EXISTS resources (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            thesis_id   INTEGER NOT NULL,
            category_id INTEGER,
            paragraph   TEXT,
            page_number TEXT,
            media_path  TEXT,
            notes       TEXT,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (thesis_id)   REFERENCES theses(id)    ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS references_tbl (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            thesis_id  INTEGER NOT NULL,
            ref_number INTEGER,
            authors    TEXT,
            title      TEXT,
            source     TEXT,
            year       TEXT,
            doi_url    TEXT,
            ref_type   TEXT DEFAULT 'article',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (thesis_id) REFERENCES theses(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS resource_references (
            resource_id  INTEGER NOT NULL,
            reference_id INTEGER NOT NULL,
            PRIMARY KEY (resource_id, reference_id),
            FOREIGN KEY (resource_id)  REFERENCES resources(id)      ON DELETE CASCADE,
            FOREIGN KEY (reference_id) REFERENCES references_tbl(id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    conn.close()


# ── Theses ────────────────────────────────────────────────────────────────────

def add_thesis(title, file_path=None, file_type=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO theses (title, file_path, file_type) VALUES (?, ?, ?)",
        (title, file_path, file_type),
    )
    conn.commit()
    thesis_id = c.lastrowid
    conn.close()
    return thesis_id


def get_all_theses():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM theses ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows


def delete_thesis(thesis_id):
    conn = get_connection()
    conn.execute("DELETE FROM theses WHERE id = ?", (thesis_id,))
    conn.commit()
    conn.close()


def update_thesis(thesis_id, title=None, file_path=None, file_type=None):
    conn = get_connection()
    fields = []
    values = []
    if title is not None:
        fields.append("title = ?")
        values.append(title)
    if file_path is not None:
        fields.append("file_path = ?")
        values.append(file_path)
    if file_type is not None:
        fields.append("file_type = ?")
        values.append(file_type)
    if fields:
        values.append(thesis_id)
        conn.execute(f"UPDATE theses SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
    conn.close()


# ── Categories ────────────────────────────────────────────────────────────────

def add_category(name, color="#3B82F6"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO categories (name, color) VALUES (?, ?)", (name, color))
    conn.commit()
    cat_id = c.lastrowid
    conn.close()
    return cat_id


def get_all_categories():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()
    return rows


def delete_category(cat_id):
    conn = get_connection()
    conn.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()


def update_category(cat_id, name=None, color=None):
    conn = get_connection()
    fields = []
    values = []
    if name is not None:
        fields.append("name = ?")
        values.append(name)
    if color is not None:
        fields.append("color = ?")
        values.append(color)
    if fields:
        values.append(cat_id)
        conn.execute(f"UPDATE categories SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
    conn.close()


# ── Resources ─────────────────────────────────────────────────────────────────

def add_resource(thesis_id, paragraph="", category_id=None, page_number="",
                 media_path=None, notes=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """INSERT INTO resources
           (thesis_id, category_id, paragraph, page_number, media_path, notes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (thesis_id, category_id, paragraph, page_number, media_path, notes),
    )
    conn.commit()
    res_id = c.lastrowid
    conn.close()
    return res_id


def get_resources(thesis_id, category_id=None, search_term=None):
    conn = get_connection()
    query = """
        SELECT r.*, c.name AS category_name, c.color AS category_color
        FROM resources r
        LEFT JOIN categories c ON r.category_id = c.id
        WHERE r.thesis_id = ?
    """
    params = [thesis_id]
    if category_id:
        query += " AND r.category_id = ?"
        params.append(category_id)
    if search_term:
        query += " AND (r.paragraph LIKE ? OR r.notes LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
    query += " ORDER BY r.created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def update_resource(res_id, **kwargs):
    conn = get_connection()
    fields = []
    values = []
    for key in ("paragraph", "category_id", "page_number", "media_path", "notes"):
        if key in kwargs:
            fields.append(f"{key} = ?")
            values.append(kwargs[key])
    if fields:
        fields.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(res_id)
        conn.execute(f"UPDATE resources SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
    conn.close()


def delete_resource(res_id):
    conn = get_connection()
    conn.execute("DELETE FROM resources WHERE id = ?", (res_id,))
    conn.commit()
    conn.close()


# ── References ────────────────────────────────────────────────────────────────

def add_reference(thesis_id, ref_number=None, authors="", title="", source="",
                  year="", doi_url="", ref_type="article"):
    conn = get_connection()
    if ref_number is None:
        row = conn.execute(
            "SELECT COALESCE(MAX(ref_number), 0) + 1 AS next_num FROM references_tbl WHERE thesis_id = ?",
            (thesis_id,),
        ).fetchone()
        ref_number = row["next_num"]
    c = conn.cursor()
    c.execute(
        """INSERT INTO references_tbl
           (thesis_id, ref_number, authors, title, source, year, doi_url, ref_type)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (thesis_id, ref_number, authors, title, source, year, doi_url, ref_type),
    )
    conn.commit()
    ref_id = c.lastrowid
    conn.close()
    return ref_id


def get_references(thesis_id, search_term=None):
    conn = get_connection()
    query = "SELECT * FROM references_tbl WHERE thesis_id = ?"
    params = [thesis_id]
    if search_term:
        query += " AND (authors LIKE ? OR title LIKE ? OR source LIKE ?)"
        params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])
    query += " ORDER BY ref_number ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def update_reference(ref_id, **kwargs):
    conn = get_connection()
    fields = []
    values = []
    for key in ("ref_number", "authors", "title", "source", "year", "doi_url", "ref_type"):
        if key in kwargs:
            fields.append(f"{key} = ?")
            values.append(kwargs[key])
    if fields:
        values.append(ref_id)
        conn.execute(f"UPDATE references_tbl SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()
    conn.close()


def delete_reference(ref_id):
    conn = get_connection()
    conn.execute("DELETE FROM references_tbl WHERE id = ?", (ref_id,))
    conn.commit()
    conn.close()


def renumber_references(thesis_id):
    """Re-assign sequential [1], [2], … numbers to all refs in a thesis."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id FROM references_tbl WHERE thesis_id = ? ORDER BY ref_number ASC",
        (thesis_id,),
    ).fetchall()
    for idx, row in enumerate(rows, start=1):
        conn.execute("UPDATE references_tbl SET ref_number = ? WHERE id = ?", (idx, row["id"]))
    conn.commit()
    conn.close()


# ── Resource ↔ Reference links ───────────────────────────────────────────────

def link_resource_reference(resource_id, reference_id):
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO resource_references (resource_id, reference_id) VALUES (?, ?)",
        (resource_id, reference_id),
    )
    conn.commit()
    conn.close()


def unlink_resource_reference(resource_id, reference_id):
    conn = get_connection()
    conn.execute(
        "DELETE FROM resource_references WHERE resource_id = ? AND reference_id = ?",
        (resource_id, reference_id),
    )
    conn.commit()
    conn.close()


def get_references_for_resource(resource_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT rt.* FROM references_tbl rt
           JOIN resource_references rr ON rt.id = rr.reference_id
           WHERE rr.resource_id = ?
           ORDER BY rt.ref_number ASC""",
        (resource_id,),
    ).fetchall()
    conn.close()
    return rows


def get_resources_for_reference(reference_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT r.* FROM resources r
           JOIN resource_references rr ON r.id = rr.resource_id
           WHERE rr.reference_id = ?
           ORDER BY r.created_at DESC""",
        (reference_id,),
    ).fetchall()
    conn.close()
    return rows
