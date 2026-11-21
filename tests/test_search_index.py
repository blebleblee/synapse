"""The search index stays in sync with lesson files and falls back to a scan when needed."""
import os
import time
from pathlib import Path

import learning_engine.search as search
import learning_engine.security as sec


def _lesson(rel: str, text: str) -> Path:
    p = Path(sec.TOPICS_DIR) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def _paths(results):
    return {(r["path"], r["file"]) for r in results}


def test_index_picks_up_new_changed_and_deleted_files():
    p = _lesson("computing/idx_cat/idx_topic/lesson_01.md", "## Intro\n\nThe zorblatt protocol.\n")
    assert search.search_curriculum("zorblatt")
    assert search.index_path().exists()

    p.write_text("## Intro\n\nNothing to see, quuxinator instead.\n", encoding="utf-8")
    os.utime(p, ns=(time.time_ns(), time.time_ns() + 10**9))
    assert search.search_curriculum("zorblatt") == []
    assert search.search_curriculum("quuxinator")

    p.unlink()
    assert search.search_curriculum("quuxinator") == []


def test_prefix_matching_and_section():
    _lesson("computing/idx_cat/pg/lesson_01.md", "# Title\n\n## Storage\n\nPostgres uses a WriteAheadLogging scheme.\n")
    res = search.search_curriculum("writeahead")
    assert res and res[0]["section"] == "Storage"


def test_index_and_scan_agree(monkeypatch):
    _lesson("computing/idx_cat/a/lesson_01.md", "## A\n\nflumox flumox here\n")
    _lesson("computing/idx_cat/b/lesson_01.md", "## B\n\nonly one flumox\n")
    indexed = search.search_curriculum("flumox")
    monkeypatch.setenv("SYNAPSE_SEARCH_INDEX", "0")
    scanned = search.search_curriculum("flumox")
    assert indexed == scanned and len(indexed) == 2


def test_punctuation_only_query_falls_back_to_scan():
    _lesson("computing/idx_cat/c/lesson_01.md", "## C\n\nuse the -- separator\n")
    assert search.search_curriculum("--")


def test_search_does_not_wait_for_first_build(monkeypatch):
    _lesson("computing/idx_cat/d/lesson_01.md", "## D\n\nblorptastic\n")
    search._ready.discard(str(search.index_path()))
    assert search._lock.acquire()
    try:  # a background build holds the lock: results still come from a scan
        assert search.search_curriculum("blorptastic")
    finally:
        search._lock.release()
