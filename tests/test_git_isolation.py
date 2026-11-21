import pytest
import subprocess
from unittest.mock import patch, MagicMock
from learning_engine.topic_manager import delete_subtopic, rename_subtopic
from learning_engine.summary import regenerate_summary
import json
import os
from app.backend.main import save_session, SaveSessionRequest, ChatMessage, compile_artifacts, QuizRequest

@patch('subprocess.run')
@patch('learning_engine.summary.get_provider')
@patch('app.backend.main.get_provider')
@patch('app.backend.main.get_chat_provider')
def test_operations_do_not_invoke_git(mock_get_chat_provider, mock_get_provider_main, mock_get_provider_summary, mock_run, tmp_path, monkeypatch):
    """
    Verify that topic mutations, summary generation, and guide compilation
    do not automatically trigger `git add`, `git commit`, or `git push`.
    """
    mock_get_chat_provider.return_value = (MagicMock(generate=MagicMock(return_value="dummy generated text")), "dummy_model")
    mock_get_provider_main.return_value = MagicMock(generate=MagicMock(return_value="dummy generated text"))
    mock_get_provider_summary.return_value = MagicMock(generate=MagicMock(return_value="dummy generated text"))

    # Create a dummy workspace
    workspace = tmp_path / "workspace"
    topics_dir = workspace / "topics"
    domain_dir = topics_dir / "test_domain"
    cat_dir = domain_dir / "test_cat"
    sub_dir = cat_dir / "test_sub"
    sub_dir.mkdir(parents=True)
    (domain_dir / "SYLLABUS.md").write_text("- **Test Sub** (`test_cat/test_sub/`)", encoding="utf-8")
    
    monkeypatch.setenv("SYNAPSE_WORKSPACE", str(workspace))
    monkeypatch.setenv("SYNAPSE_TOPICS_DIR", str(topics_dir))

    # 1. Regenerate Summary
    regenerate_summary("test_domain/test_cat/test_sub")
    
    # 2. Compile Guide
    # Need to create dummy lessons
    (sub_dir / "lesson_01.md").write_text("# Lesson 1", encoding="utf-8")
    req = QuizRequest(query="test_domain/test_cat/test_sub")
    compile_artifacts(req)
    
    # 3. Save Session
    req_save = SaveSessionRequest(query="test_domain/test_cat/test_sub", history=[ChatMessage(role="student", content="hello")])
    save_session(req_save)

    # 4. Rename Subtopic
    rename_subtopic("test_domain/test_cat/test_sub", "New Title")
    
    # 5. Delete Subtopic
    delete_subtopic("test_domain/test_cat/test_sub")

    # Verify subprocess.run was NEVER called with "git"
    for call in mock_run.call_args_list:
        args = call[0][0]
        if isinstance(args, list) and args and args[0] == "git":
            pytest.fail(f"git command was unexpectedly executed: {args}")
