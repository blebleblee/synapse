"""get_chat_provider routing regressions from the FIND-75 refactor (8901d75)."""
from unittest.mock import patch

import learning_engine.models as models


def test_cloud_mentor_does_not_probe_the_ollama_cluster(monkeypatch):
    # Before 8901d75 a Claude mentor returned before any cluster probe; the
    # refactor probed every node first, delaying every mentor reply.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    with patch.object(models, "get_settings", return_value={}), \
         patch.object(models.OllamaCluster, "get_cluster_status",
                      side_effect=AssertionError("cluster probed")):
        provider, name = models.get_chat_provider(model="claude-sonnet-5-5")
    assert isinstance(provider, models.AnthropicProvider) and name == "claude-sonnet-5-5"


def test_unreachable_model_on_chosen_host_is_not_swapped_for_another_there():
    # host + model given, the model does not answer: look for the model on the
    # cluster, don't silently use whatever else that host has.
    status = {"http://other:11434": {"online": True, "models": ["wanted:7b"]}}
    with patch.object(models, "get_settings", return_value={}), \
         patch.object(models.OllamaProvider, "check_connectivity", return_value=False), \
         patch.object(models.OllamaProvider, "is_available", return_value=True), \
         patch.object(models.OllamaProvider, "list_models", return_value=["other:3b"]), \
         patch.object(models.OllamaCluster, "get_cluster_status", return_value=status):
        provider, name = models.get_chat_provider(model="wanted:7b", host="http://chosen:11434")
    assert name == "wanted:7b" and provider.host == "http://other:11434"
