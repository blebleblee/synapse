"""scripts/sync_addons.py copies only allowed files, never over newer ones, never deletes."""
import importlib.util
import os
from pathlib import Path

spec = importlib.util.spec_from_file_location("sync_addons", Path(__file__).resolve().parent.parent / "scripts" / "sync_addons.py")
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


def write(path: Path, text: str, mtime: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    os.utime(path, (mtime, mtime))


def test_plan_copies_missing_and_older_only(tmp_path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    write(src / "d/a/lesson_01.md", "new", 200)
    write(dst / "d/a/lesson_01.md", "old", 100)      # source newer -> copy
    write(src / "d/a/lesson_02.md", "stale", 100)
    write(dst / "d/a/lesson_02.md", "edited", 200)   # target newer -> keep
    write(src / "d/a/labs.md", "same", 100)
    write(dst / "d/a/labs.md", "same", 300)          # identical -> skip
    write(src / "d/b/lesson_01.md", "fresh", 100)    # missing in target -> copy
    write(dst / "d/c/lesson_01.md", "only", 100)     # only in target -> report, keep

    plan = sync.make_plan(src, dst, lambda rel: True)
    assert plan.copy == ["d/a/lesson_01.md", "d/b/lesson_01.md"]
    assert plan.target_newer == ["d/a/lesson_02.md"]
    assert plan.only_in_target == ["d/c/lesson_01.md"]
    assert plan.same == 1

    sync.apply_plan(plan, src, dst)
    assert (dst / "d/a/lesson_01.md").read_text() == "new"
    assert (dst / "d/a/lesson_02.md").read_text() == "edited"
    assert (dst / "d/c/lesson_01.md").exists()

    forced = sync.make_plan(src, dst, lambda rel: True, force=True)
    assert "d/a/lesson_02.md" in forced.copy


def test_plan_skips_disallowed_and_private_session_files(tmp_path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    dst.mkdir()
    write(src / "public/a/lesson_01.md", "x", 100)
    write(src / "private/a/lesson_01.md", "x", 100)
    write(src / "private/a/sessions/s1.md", "chat", 100)
    write(src / "private/a/active_session.md", "chat", 100)
    write(src / "private/a/chat_history.json", "[]", 100)
    write(src / "private/a/artifacts/MASTERED_GUIDE.md", "old", 100)
    write(src / "private/a/__pycache__/x.pyc", "b", 100)

    plan = sync.make_plan(src, dst, lambda rel: rel.startswith("private/"))
    assert plan.copy == ["private/a/lesson_01.md"]


def test_tracked_paths_never_count_as_ignored():
    # `git check-ignore --no-index` also reports tracked files matching an ignore
    # rule; those belong to synapse and must not be synced.
    lines = ["topics/private/a/lesson_01.md", "topics/languages/germanic/x/lesson_01.md", ""]
    tracked = {"topics/languages/germanic/x/lesson_01.md"}
    assert sync.filter_ignored(lines, tracked) == {"private/a/lesson_01.md"}
