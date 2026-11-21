"""
Acceptance and Regression Tests for Curriculum Generation Pipeline
Covers:
1. Full subtopic generation with deterministic mock providers.
2. Partial-result persistence: completed modules are preserved when later modules fail.
3. Resuming generation (force=False) generates only missing modules.
4. Force regeneration (force=True) purges and regenerates all modules.
5. Quality gate invariants: refusal detection, length threshold, and terminal punctuation.
"""

import pytest
from pathlib import Path
from learning_engine.security import TOPICS_DIR
from learning_engine.models import LLMProvider, validate_lesson_completeness
from learning_engine.generator import generate_subtopic_content

VALID_LESSON_BODY = (
    "# Masterclass Chapter: Architectural Invariants\n\n"
    "The foundation of reliable systems design lies in explicit formal guarantees. "
    "When designing storage engines, state transitions must adhere strictly to ACID properties, "
    "ensuring that writes either commit atomically to non-volatile storage or rollback completely. "
    "Write-Ahead Logging (WAL) guarantees that before any dirty page is flushed from buffer memory "
    "to table storage, the corresponding log sequence record has been fsynced to disk. "
    "This fundamental ordering invariant ensures crash consistency across arbitrary power failures.\n\n"
    "## Mechanical Sympathy & Page Layout\n\n"
    "Modern storage engines organize persistent data into fixed-size slotted pages, typically 8KB in size. "
    "Each page contains a header, an array of item pointers growing downward, and raw tuple storage "
    "growing upward from the bottom of the page. This bi-directional allocation avoids fragmentation "
    "and allows variable-length tuples to be referenced by stable internal slot numbers. "
    "Understanding memory hierarchy, L1/L2 cache lines, and sequential disk bandwidth allows engineers "
    "to design data structures that maximize hardware utilization while avoiding excessive lock contention.\n\n"
    "```bash\n"
    "# Inspect physical page allocation and alignment\n"
    "pg_controldata /var/lib/postgresql/data\n"
    "```\n\n"
    "## Operational Invariants & Failure Recovery\n\n"
    "During recovery from an unclean shutdown, the database scans the WAL from the latest consistent checkpoint. "
    "Redo processing replays all logged changes to ensure durability, while undo processing rolls back uncommitted transactions. "
    "Through rigorous mechanical invariants, data integrity is guaranteed under all operating conditions."
)

class DeterministicMockProvider(LLMProvider):
    def __init__(self, fail_on=None):
        self.model = "claude-sonnet-5"
        self.fail_on = fail_on
        self.call_count = 0
        self.generated_prompts = []

    def generate(self, prompt, **kwargs):
        self.call_count += 1
        self.generated_prompts.append(prompt)
        if self.fail_on and self.fail_on in prompt:
            raise RuntimeError(f"Simulated generation failure for {self.fail_on}")
        return VALID_LESSON_BODY

def test_generate_subtopic_all_success(tmp_path):
    """Verifies that all modules are generated, validated, and persisted on disk."""
    subtopic_dir = TOPICS_DIR / "computing" / "data" / "postgresql"
    subtopic_dir.mkdir(parents=True, exist_ok=True)

    provider = DeterministicMockProvider()
    results = generate_subtopic_content(
        domain="computing",
        category="data",
        subtopic_id="postgresql",
        subtopic_dir=subtopic_dir,
        provider=provider,
        force=True
    )

    assert len(results) >= 2
    assert all(results.values()), f"Expected all modules to succeed, got: {results}"

    # Verify files on disk
    lesson_files = list(subtopic_dir.glob("lesson_*.md"))
    assert len(lesson_files) >= 1
    for f in lesson_files:
        assert f.stat().st_size > 500
        content = f.read_text(encoding="utf-8")
        assert "Masterclass Chapter" in content

def test_generate_subtopic_partial_failure_and_resume(tmp_path):
    """
    Verifies that when a module fails during generation:
    1. Succeeded modules remain safely persisted on disk.
    2. Failed module is not written and marked False in results.
    3. Re-running with force=False resumes and generates only the missing module.
    """
    subtopic_dir = TOPICS_DIR / "computing" / "data" / "postgresql"
    subtopic_dir.mkdir(parents=True, exist_ok=True)

    # Clean existing markdown files first
    for f in subtopic_dir.glob("*.md"):
        f.unlink()

    # Provider fails specifically on lesson 2
    failing_provider = DeterministicMockProvider(fail_on="Lesson 2")
    results1 = generate_subtopic_content(
        domain="computing",
        category="data",
        subtopic_id="postgresql",
        subtopic_dir=subtopic_dir,
        provider=failing_provider,
        force=True
    )

    # Find lesson 1 and lesson 2 filenames
    lesson_01 = next((k for k in results1.keys() if "01" in k or "lesson_01" in k), None)
    lesson_02 = next((k for k in results1.keys() if "02" in k or "lesson_02" in k), None)

    assert lesson_01 is not None
    assert results1[lesson_01] is True
    assert (subtopic_dir / lesson_01).exists()

    if lesson_02:
        assert results1[lesson_02] is False
        assert not (subtopic_dir / lesson_02).exists()

    # Step 2: Resume generation with working provider and force=False
    working_provider = DeterministicMockProvider()
    results2 = generate_subtopic_content(
        domain="computing",
        category="data",
        subtopic_id="postgresql",
        subtopic_dir=subtopic_dir,
        provider=working_provider,
        force=False
    )

    # Lesson 01 was already on disk and skipped (marked False in tasks)
    assert results2.get(lesson_01) is False
    # Lesson 02 was generated
    if lesson_02:
        assert results2.get(lesson_02) is True
        assert (subtopic_dir / lesson_02).exists()

def test_generate_subtopic_force_regeneration(tmp_path):
    """Verifies that force=True purges and overwrites existing stale drafts."""
    subtopic_dir = TOPICS_DIR / "computing" / "data" / "postgresql"
    subtopic_dir.mkdir(parents=True, exist_ok=True)

    target_file = subtopic_dir / "lesson_01_foundations_and_invariants.md"
    target_file.write_text("STALE_CORRUPTED_OLD_DRAFT", encoding="utf-8")

    provider = DeterministicMockProvider()
    generate_subtopic_content(
        domain="computing",
        category="data",
        subtopic_id="postgresql",
        subtopic_dir=subtopic_dir,
        provider=provider,
        force=True
    )

    new_content = target_file.read_text(encoding="utf-8")
    assert "STALE_CORRUPTED_OLD_DRAFT" not in new_content
    assert "Masterclass Chapter" in new_content

def test_validate_lesson_completeness_quality_gates():
    """Verifies quality gate invariants: rejection of refusals, stubs, and truncations."""
    # 1. Rejects model refusals
    with pytest.raises(ValueError, match="Model refusal detected"):
        validate_lesson_completeness("I apologize, but I cannot proceed with this request.")

    # 2. Rejects stubs that are too short (<1200 characters)
    with pytest.raises(ValueError, match="too short/incomplete"):
        validate_lesson_completeness("# Short Lesson\nOnly two sentences.")

    # 3. Rejects output cut off without valid terminal punctuation
    cut_off_text = VALID_LESSON_BODY.rstrip(".!") + " and the process then"
    with pytest.raises(ValueError, match="Truncated output"):
        validate_lesson_completeness(cut_off_text)

    # 4. Valid content passes untouched
    assert validate_lesson_completeness(VALID_LESSON_BODY) == VALID_LESSON_BODY
