"""
Full-Text Search Engine
Indexes and searches across all generated curriculum markdown units.

Searches use a SQLite FTS5 index stored next to the app database
(search_index.db). The index keeps itself current: before each query it
compares file sizes and modification times with what it indexed and re-reads
only files that changed, so there is no separate rebuild step. Lesson text is
not copied into the index (contentless table); snippets are read from the
lesson files of the top candidates only.

A plain scan over every file is kept as a fallback: it is used while the index
is first being built in the background, for queries FTS5 cannot express, and
when SYNAPSE_SEARCH_INDEX=0.

Matching is by word prefix ("sql" finds "SQLite", "kube" finds "kubernetes"),
case-insensitive, any word of the query.
"""

import os
import re
import sqlite3
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional

from .security import WORKSPACE_ROOT, TOPICS_DIR

SKIP_FILES = {"GEMINI.md", "SYLLABUS.md"}
_SCHEMA_VERSION = "1"
# How many index hits are re-scored with the detailed (match count) scorer.
_CANDIDATES = 120

_lock = threading.Lock()
_ready: set = set()


def clean_snippet(text: str, match_pos: int, snippet_len: int = 160) -> str:
    start = max(0, match_pos - snippet_len // 2)
    end = min(len(text), match_pos + snippet_len // 2)
    snippet = text[start:end].replace("\n", " ").strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet


def _topics_dir() -> Path:
    return Path(TOPICS_DIR)


def _result_for(md_path: Path, content: str, regex_pattern, query: str) -> Optional[Dict[str, Any]]:
    matches = list(regex_pattern.finditer(content))
    if not matches:
        return None

    # Deduce hierarchy (domain / discipline / topic / file.md)
    rel_parts = md_path.relative_to(_topics_dir()).parts
    if len(rel_parts) >= 3:
        domain, category, subtopic = rel_parts[0], rel_parts[1], rel_parts[2]
    else:
        domain = rel_parts[0] if len(rel_parts) > 0 else ""
        category = rel_parts[1] if len(rel_parts) > 1 else ""
        subtopic = md_path.stem

    first_match = matches[0]
    snippet = clean_snippet(content, first_match.start())

    prev_headers = re.findall(r"^#{1,3}\s+(.+)$", content[:first_match.start()], re.MULTILINE)
    section = prev_headers[-1] if prev_headers else "Introduction"

    score = len(matches) * 10
    if query.lower() in subtopic.lower():
        score += 50
    if query.lower() in content.lower():
        score += 20

    return {
        "domain": domain,
        "category": category,
        "subtopic": subtopic,
        "level": "masterclass",
        "file": md_path.name,
        "path": f"{domain}/{category}/{subtopic}",
        "section": section,
        "snippet": snippet,
        "match_count": len(matches),
        "score": score,
    }


def _iter_markdown(root: Path):
    for md_path in root.glob("**/*.md"):
        if md_path.name not in SKIP_FILES:
            yield md_path


def _rank(paths, regex_pattern, query: str, max_results: int) -> List[Dict[str, Any]]:
    results = []
    for md_path in paths:
        try:
            content = md_path.read_text(encoding="utf-8")
        except Exception:
            continue
        r = _result_for(md_path, content, regex_pattern, query)
        if r:
            results.append(r)
    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:max_results]


# --- index -----------------------------------------------------------------------

def index_path() -> Path:
    custom = os.environ.get("SYNAPSE_SEARCH_INDEX_PATH")
    if custom:
        return Path(custom)
    from .database import get_db_path
    return get_db_path().parent / "search_index.db"


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def _ensure_schema(conn: sqlite3.Connection, root: Path) -> None:
    conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
    meta = dict(conn.execute("SELECT key, value FROM meta").fetchall())
    if meta.get("schema") != _SCHEMA_VERSION or meta.get("root") != str(root):
        # Different topics folder or format: start over.
        conn.execute("DROP TABLE IF EXISTS files")
        conn.execute("DROP TABLE IF EXISTS fts")
        conn.execute("DELETE FROM meta")
        conn.executemany("INSERT INTO meta VALUES (?, ?)",
                         [("schema", _SCHEMA_VERSION), ("root", str(root))])
    conn.execute("CREATE TABLE IF NOT EXISTS files ("
                 "id INTEGER PRIMARY KEY, path TEXT UNIQUE NOT NULL, mtime_ns INTEGER, size INTEGER)")
    conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS fts USING fts5("
                 "body, content='', contentless_delete=1, "
                 "tokenize='unicode61 remove_diacritics 0')")
    conn.commit()


def refresh_index(path: Optional[Path] = None) -> Dict[str, int]:
    """Bring the index in line with the topics folder. Returns change counts."""
    path = path or index_path()
    root = _topics_dir()
    conn = _connect(path)
    try:
        _ensure_schema(conn, root)
        current = {}
        for md_path in _iter_markdown(root):
            try:
                st = md_path.stat()
            except OSError:
                continue
            current[md_path.relative_to(root).as_posix()] = (st.st_mtime_ns, st.st_size)

        known = {p: (i, m, s) for i, p, m, s in conn.execute("SELECT id, path, mtime_ns, size FROM files")}
        removed = [known[p][0] for p in known.keys() - current.keys()]
        changed = [p for p, sig in current.items() if p not in known or known[p][1:] != sig]

        with conn:
            for file_id in removed:
                conn.execute("DELETE FROM fts WHERE rowid = ?", (file_id,))
                conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
            for rel in changed:
                try:
                    body = (root / rel).read_text(encoding="utf-8")
                except Exception:
                    body = ""
                mtime_ns, size = current[rel]
                if rel in known:
                    file_id = known[rel][0]
                    conn.execute("DELETE FROM fts WHERE rowid = ?", (file_id,))
                    conn.execute("UPDATE files SET mtime_ns = ?, size = ? WHERE id = ?", (mtime_ns, size, file_id))
                else:
                    file_id = conn.execute("INSERT INTO files (path, mtime_ns, size) VALUES (?, ?, ?)",
                                           (rel, mtime_ns, size)).lastrowid
                conn.execute("INSERT INTO fts (rowid, body) VALUES (?, ?)", (file_id, body))
        return {"files": len(current), "updated": len(changed), "removed": len(removed)}
    finally:
        conn.close()


def warm_index_in_background() -> threading.Thread:
    """Build/refresh the index without blocking startup; returns the thread."""
    def _run():
        try:
            with _lock:
                refresh_index()
                _ready.add(str(index_path()))
        except Exception as e:
            print(f"[!] Search index build failed, falling back to full scans: {e}", flush=True)
    thread = threading.Thread(target=_run, name="search-index", daemon=True)
    thread.start()
    return thread


def _fts_query(raw_tokens: List[str]) -> str:
    return " OR ".join('"' + t.replace('"', '""') + '"*' for t in raw_tokens)


def _indexed_candidates(raw_tokens: List[str]) -> Optional[List[Path]]:
    """Candidate files from the index, or None when the index can't be used right now."""
    if os.environ.get("SYNAPSE_SEARCH_INDEX", "1") == "0":
        return None
    if not all(re.search(r"\w", t) for t in raw_tokens):
        return None  # the index only holds words; "--" or "+=" need a scan
    path = index_path()
    key = str(path)
    # While the first build runs in another thread, don't wait for it: scan instead.
    if not _lock.acquire(blocking=key in _ready):
        return None
    try:
        refresh_index(path)
        _ready.add(key)
    except Exception:
        return None
    finally:
        _lock.release()

    root = _topics_dir()
    conn = _connect(path)
    try:
        rows = conn.execute(
            "SELECT f.path FROM fts JOIN files f ON f.id = fts.rowid "
            "WHERE fts MATCH ? ORDER BY rank LIMIT ?",
            (_fts_query(raw_tokens), _CANDIDATES),
        ).fetchall()
    except sqlite3.Error:
        return None  # e.g. a query made only of punctuation
    finally:
        conn.close()
    return [root / p for (p,) in rows]


def search_curriculum(query: str, max_results: int = 25) -> List[Dict[str, Any]]:
    if not query or len(query.strip()) < 2:
        return []

    raw_tokens = [t.strip() for t in query.strip().split() if t.strip()]
    if not raw_tokens:
        return []

    regex_pattern = re.compile("|".join(re.escape(t) for t in raw_tokens), re.IGNORECASE)

    candidates = _indexed_candidates(raw_tokens)
    if candidates is None:
        candidates = _iter_markdown(_topics_dir())
    return _rank(candidates, regex_pattern, query, max_results)
