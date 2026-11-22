"""
Tests for learning_engine.graph
Verifies DAG generation, edge validity, and topic dependency resolution.
"""

import pytest
from learning_engine.graph import get_prerequisite_graph, get_topic_dependencies

def test_get_prerequisite_graph_validity():
    graph = get_prerequisite_graph()
    assert "nodes" in graph
    assert "edges" in graph
    assert graph["node_count"] >= 500
    assert graph["edge_count"] >= 400

    nodes = graph["nodes"]
    edges = graph["edges"]

    node_ids = {n["id"] for n in nodes}

    # Verify every edge points from a valid node to a valid node
    for edge in edges:
        assert edge["source"] in node_ids, f"Broken source: {edge['source']}"
        assert edge["target"] in node_ids, f"Broken target: {edge['target']}"
        assert edge["source"] != edge["target"], "Self-loop edge found!"

    # Verify node metadata
    first_node = nodes[0]
    assert "id" in first_node
    assert "label" in first_node
    assert "domain" in first_node
    assert "color" in first_node
    assert "degree" in first_node

def test_get_topic_dependencies_known_topic():
    # LLMs should have deep_learning as prereq and ai_agents as unlock
    path = "computing/ai/large_language_models"
    deps = get_topic_dependencies(path)

    assert "target" in deps
    assert "prerequisites" in deps
    assert "unlocks" in deps

    assert len(deps["prerequisites"]) >= 1
    assert len(deps["unlocks"]) >= 1

    prereq_ids = [p["id"] for p in deps["prerequisites"]]
    assert any("deep_learning" in pid for pid in prereq_ids)

    unlock_ids = [u["id"] for u in deps["unlocks"]]
    assert any("ai_agents" in uid for uid in unlock_ids)

def test_get_topic_dependencies_non_existent():
    deps = get_topic_dependencies("non_existent_domain/fake/path")
    assert deps["prerequisites"] == []
    assert deps["unlocks"] == []


def test_node_labels_do_not_repeat_the_course_name():
    """Single-unit courses showed "Kubernetes: Kubernetes" in the course-path
    links; the course part also lost its capitalization ("Ebpf")."""
    graph = get_prerequisite_graph()
    doubled = []
    for n in graph["nodes"]:
        head, sep, tail = n["label"].partition(": ")
        if sep and head.strip().lower() == tail.strip().lower():
            doubled.append(n["label"])
    assert doubled == [], f"{len(doubled)} doubled labels, e.g. {doubled[:3]}"
