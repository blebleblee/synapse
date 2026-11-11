"""
Tests for learning_engine.topic_manager
Verifies 4-level taxonomy, path sanitization, and subtopic resolution.
"""

import pytest
from pathlib import Path
from learning_engine.topic_manager import (
    get_topic_tree,
    resolve_subtopic,
    sanitize_rel_path,
    get_domain_persona,
    TOPICS_DIR
)

def test_get_topic_tree_structure():
    tree = get_topic_tree()
    assert isinstance(tree, dict)
    assert len(tree) >= 11

    # Verify computing domain structure
    assert "computing" in tree
    comp = tree["computing"]
    assert "disciplines" in comp
    disciplines = comp["disciplines"]
    assert "infrastructure" in disciplines

    infra = disciplines["infrastructure"]
    assert "courses" in infra
    assert "kubernetes" in infra["courses"]

    k8s = infra["courses"]["kubernetes"]
    assert "units" in k8s
    assert len(k8s["units"]) >= 1

    # Verify course display name and PostgreSQL Internals
    assert "data" in disciplines
    assert "postgresql" in disciplines["data"]["courses"]
    pg_course = disciplines["data"]["courses"]["postgresql"]
    assert pg_course["display_name"] == "PostgreSQL Internals"

    # Verify unit node properties
    first_unit = next(iter(k8s["units"].values()))
    assert "rel_path" in first_unit
    assert "display_name" in first_unit
    assert "course_title" in first_unit
    assert "status" in first_unit
    assert "complete" in first_unit["status"]

def test_sanitize_rel_path_valid():
    p = sanitize_rel_path("computing/infrastructure/kubernetes/01_control_plane_and_etcd")
    assert p.is_relative_to(TOPICS_DIR)

def test_sanitize_rel_path_traversal_attack():
    with pytest.raises(ValueError):
        sanitize_rel_path("../../etc/passwd")

    with pytest.raises(ValueError):
        sanitize_rel_path("../../../../../root")

def test_resolve_subtopic_exact():
    res = resolve_subtopic("computing/infrastructure/kubernetes/01_control_plane_and_etcd")
    assert res is not None
    domain, cat, sub, sub_path = res
    assert domain == "computing"
    assert cat == "infrastructure/kubernetes"
    assert sub == "01_control_plane_and_etcd"
    assert sub_path.exists()

def test_resolve_subtopic_partial():
    res = resolve_subtopic("control_plane_and_etcd")
    assert res is not None
    domain, cat, sub, sub_path = res
    assert domain == "computing"

def test_resolve_subtopic_non_existent():
    res = resolve_subtopic("totally_fictional_non_existent_topic_12345")
    assert res is None

def test_get_domain_persona():
    persona = get_domain_persona("computing")
    assert "Software Architect" in persona or "Systems" in persona

    persona_unknown = get_domain_persona("unknown_domain")
    assert "technical mentor" in persona_unknown.lower()

def test_get_unit_lessons_postgresql():
    from learning_engine.topic_manager import get_unit_lessons, TOPICS_DIR
    pg_dir = TOPICS_DIR / "computing" / "data" / "postgresql"
    lessons = get_unit_lessons(pg_dir)
    assert len(lessons) == 6
    assert lessons[0]["id"] == "lesson_01_foundations_and_invariants"
    assert "Lesson 1: Foundations" in lessons[0]["title"]
