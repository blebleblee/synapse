"""Computing courses get lab and lesson sections about their own subject.

Before: every course in computing/software, computing/systems and any
unmatched category got the compiler blueprint, whose fixed lab sections
(AST/IR disassembly, cache-miss profiling, data-race sanitizers) produced a
C++ compiler lab for Bash. Uses the git-tracked public course list only.
"""
import subprocess
from pathlib import Path

import pytest

from learning_engine.domain_strategies import (GLOBAL_REGISTRY, LOW_LEVEL_COMPUTING_COURSES,
                                               build_topic_modules)

ROOT = Path(__file__).resolve().parents[1]
COMPILER_MARKERS = ("AST, IR", "Disassembly", "Cache Miss", "Data Race", "Leak Sanitizer", "Struct Packing")


def _computing_courses():
    out = subprocess.run(["git", "ls-files", "topics/computing"], cwd=ROOT, capture_output=True, text=True).stdout
    return sorted({tuple(Path(f).parts[1:4]) for f in out.split() if f.endswith("/labs.md")})


COURSES = _computing_courses()


def test_course_list_is_not_empty():
    assert len(COURSES) > 100


@pytest.mark.parametrize("domain,category,sub", [c for c in COURSES if c[2] not in LOW_LEVEL_COMPUTING_COURSES])
def test_no_compiler_sections_outside_low_level_courses(domain, category, sub):
    title = sub.replace("_", " ").title()
    for m in build_topic_modules(domain, category, sub, title):
        for marker in COMPILER_MARKERS:
            assert marker not in m["prompt"], f"{sub}/{m['filename']} asks for '{marker}'"


@pytest.mark.parametrize("sub", sorted(LOW_LEVEL_COMPUTING_COURSES))
def test_low_level_courses_keep_the_compiler_blueprint(sub):
    labs = build_topic_modules("computing", "software", sub, sub.title())[-1]
    assert "AST, IR" in labs["prompt"]


def test_general_software_labs_name_the_course():
    labs = build_topic_modules("computing", "systems", "bash", "Bash")[-1]
    assert "Exercise 1: Build Something Small With Bash" in labs["prompt"]
