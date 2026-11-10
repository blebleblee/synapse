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
    assert graph["node_count"] >= 700
    assert graph["edge_count"] >= 500

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
    # LLMs unit 02 should have unit 01 as prereq and unit 03 as unlock
    path = "computing/ai/large_language_models/02_instruction_tuning_and_rlhf"
    deps = get_topic_dependencies(path)

    assert "target" in deps
    assert "prerequisites" in deps
    assert "unlocks" in deps

    assert len(deps["prerequisites"]) >= 1
    assert len(deps["unlocks"]) >= 1

    prereq_ids = [p["id"] for p in deps["prerequisites"]]
    assert any("01_tokenization" in pid for pid in prereq_ids)

    unlock_ids = [u["id"] for u in deps["unlocks"]]
    assert any("03_parameter_efficient" in uid for uid in unlock_ids)

def test_get_topic_dependencies_non_existent():
    deps = get_topic_dependencies("non_existent_domain/fake/path")
    assert deps["prerequisites"] == []
    assert deps["unlocks"] == []
