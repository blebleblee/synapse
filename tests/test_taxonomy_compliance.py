"""
Tests for Strict 3-Level Curriculum Taxonomy Compliance
Read-only repository taxonomy audit inspecting the real repository curriculum.
Guarantees that:
1. Zero numbered directories (e.g. 01_*, 02_*) exist anywhere in the repository curriculum.
2. All lesson files (lesson_*.md) and labs (labs.md) are strictly at depth 3:
   topics/{domain}/{discipline}/{topic}/{file}
3. All 12 SYLLABUS.md files contain strictly 2-segment relative paths (discipline/topic/).
4. Any attempt to pass an invalid, deep, or numbered path into validate_canonical_topic_path
   raises an immediate ValueError.
5. Zero legacy foundation files or level directories exist in the curriculum.
"""

import re
import pytest
from pathlib import Path
from learning_engine.security import validate_canonical_topic_path

# Explicitly inspect the real repository curriculum independently of workspace overrides
REPO_ROOT = Path(__file__).resolve().parent.parent
REPO_TOPICS_DIR = (REPO_ROOT / "topics").resolve()


def test_audit_targets_real_repository_curriculum():
    """Verify that taxonomy audits explicitly target the real repository curriculum, not temporary fixtures."""
    assert REPO_TOPICS_DIR.exists()
    assert REPO_TOPICS_DIR.is_dir()
    assert REPO_TOPICS_DIR == (REPO_ROOT / "topics").resolve()

    # Verify it contains rich repository curriculum content, not minimal test fixtures
    syllabus_files = list(REPO_TOPICS_DIR.glob("*/SYLLABUS.md"))
    assert len(syllabus_files) >= 12

    # Verify repository topics contains full curriculum content across all domains
    all_lessons = list(REPO_TOPICS_DIR.rglob("lesson_*.md"))
    assert len(all_lessons) > 100


def test_zero_numbered_directories():
    """Verify zero numbered directories exist anywhere under the repository topics/."""
    numbered_dirs = [
        str(d.relative_to(REPO_TOPICS_DIR))
        for d in REPO_TOPICS_DIR.rglob("*")
        if d.is_dir() and re.match(r"^\d{2}_", d.name)
    ]
    assert len(numbered_dirs) == 0, f"Found residual numbered directories on disk: {numbered_dirs}"


def test_all_lesson_files_at_canonical_depth():
    """Verify all lesson and lab files are located strictly at depth 3 under repository topics/."""
    violating_files = []
    for f in REPO_TOPICS_DIR.rglob("*.md"):
        if f.name in ("SYLLABUS.md", "GEMINI.md", "SUMMARY.md", "CURRICULUM_BLUEPRINT.md"):
            continue
        if "sessions" in f.parts or f.name.startswith("active_session"):
            continue
        rel = f.relative_to(REPO_TOPICS_DIR)
        parts = rel.parts
        # parts must be: (domain, discipline, topic, filename) -> length 4
        if len(parts) != 4:
            violating_files.append((str(rel), len(parts)))
        for seg in parts[:-1]:
            if re.match(r"^\d{2}_", seg):
                violating_files.append((str(rel), f"numbered_segment:{seg}"))

    assert len(violating_files) == 0, f"Files violating 3-level taxonomy: {violating_files}"


def test_syllabi_have_zero_deep_or_numbered_paths():
    """Verify all 12 SYLLABUS.md files strictly contain 2-segment relative paths (discipline/topic/)."""
    syllabus_files = list(REPO_TOPICS_DIR.glob("*/SYLLABUS.md"))
    assert len(syllabus_files) >= 12, f"Expected at least 12 SYLLABUS.md files, found {len(syllabus_files)}"

    invalid_entries = []
    for s_file in syllabus_files:
        content = s_file.read_text(encoding="utf-8")
        matches = re.findall(r"\(\`([^`]+)/\`\)", content)
        for rel_path in matches:
            parts = rel_path.split("/")
            if len(parts) != 2:
                invalid_entries.append((s_file.parent.name, rel_path, f"segment_count_{len(parts)}"))
            for p in parts:
                if re.match(r"^\d{2}_", p):
                    invalid_entries.append((s_file.parent.name, rel_path, "has_numbered_prefix"))

    assert len(invalid_entries) == 0, f"Syllabus entries violating 2-segment taxonomy: {invalid_entries}"


def test_validate_canonical_topic_path_enforcement():
    """Verify path validator rejects invalid depths and accepts canonical paths."""
    # 1. Valid canonical 3-level paths
    valid_p1 = REPO_TOPICS_DIR / "computing" / "systems" / "bash"
    assert validate_canonical_topic_path(valid_p1, base_topics_dir=REPO_TOPICS_DIR) == valid_p1.resolve()

    valid_p2 = REPO_TOPICS_DIR / "arts" / "music_performance" / "bass_guitar"
    assert validate_canonical_topic_path(valid_p2, base_topics_dir=REPO_TOPICS_DIR) == valid_p2.resolve()

    valid_p3 = REPO_TOPICS_DIR / "computing" / "infrastructure" / "kubernetes"
    assert validate_canonical_topic_path(valid_p3, base_topics_dir=REPO_TOPICS_DIR) == valid_p3.resolve()

    # 2. Too shallow (2 levels: domain/discipline)
    shallow_p = REPO_TOPICS_DIR / "computing" / "infrastructure"
    with pytest.raises(ValueError, match="Taxonomy violation"):
        validate_canonical_topic_path(shallow_p, base_topics_dir=REPO_TOPICS_DIR)

    # 3. Too deep (4 levels: domain/discipline/topic/unit)
    deep_p1 = REPO_TOPICS_DIR / "computing" / "infrastructure" / "kubernetes" / "01_control_plane_and_etcd"
    with pytest.raises(ValueError, match="Taxonomy violation"):
        validate_canonical_topic_path(deep_p1, base_topics_dir=REPO_TOPICS_DIR)

    deep_p2 = REPO_TOPICS_DIR / "arts" / "music_performance" / "bass_guitar" / "02_rhythm_muting_and_grooves"
    with pytest.raises(ValueError, match="Taxonomy violation"):
        validate_canonical_topic_path(deep_p2, base_topics_dir=REPO_TOPICS_DIR)

    # 4. Numbered prefix in topic name
    numbered_p = REPO_TOPICS_DIR / "arts" / "music_performance" / "01_bass_guitar"
    with pytest.raises(ValueError, match="Taxonomy violation"):
        validate_canonical_topic_path(numbered_p, base_topics_dir=REPO_TOPICS_DIR)


def test_zero_duplicate_lesson_numbers():
    """Verify no topic directory contains multiple files with the same lesson index."""
    duplicate_violations = []
    for topic_dir in sorted(REPO_TOPICS_DIR.rglob("*")):
        if not topic_dir.is_dir():
            continue
        lessons = list(topic_dir.glob("lesson_*.md"))
        if not lessons:
            continue
        by_num = {}
        for l in lessons:
            m = re.match(r"^lesson_(\d{2})_", l.name)
            if m:
                num = m.group(1)
                by_num.setdefault(num, []).append(l.name)

        dupes = {num: files for num, files in by_num.items() if len(files) > 1}
        if dupes:
            duplicate_violations.append((str(topic_dir.relative_to(REPO_TOPICS_DIR)), dupes))

    assert len(duplicate_violations) == 0, f"Found topics with duplicate lesson numbers: {duplicate_violations}"


def test_zero_foundation_files():
    """Verify absolutely zero legacy FOUNDATION.md files exist in the curriculum."""
    foundations = [str(f.relative_to(REPO_TOPICS_DIR)) for f in REPO_TOPICS_DIR.rglob("*.md") if f.name.lower() == "foundation.md"]
    assert len(foundations) == 0, f"Found legacy FOUNDATION.md files: {foundations}"


def test_zero_legacy_level_directories():
    """Verify no legacy beginner/intermediate/advanced directories exist anywhere in repository topics/."""
    level_dirs = []
    for d in REPO_TOPICS_DIR.rglob("*"):
        if d.is_dir() and d.name.lower() in ["beginner", "intermediate", "advanced"]:
            level_dirs.append(str(d.relative_to(REPO_TOPICS_DIR)))
    assert len(level_dirs) == 0, f"Found legacy level directories: {level_dirs}"
