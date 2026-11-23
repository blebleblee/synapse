"""
Every provider must accept the call the lesson generator makes:
`generate(prompt, system_instruction=..., max_tokens=8192)`.
Only AnthropicProvider did, so generation with Ollama, an Ollama cluster or
Gemini failed every attempt with "unexpected keyword argument 'max_tokens'"
(the test fakes and conftest's network blocker take **kwargs, which hid it).

conftest replaces every provider's `generate` with a catch-all stub, so the
real methods are captured here at import time, before that fixture runs.
Network calls are stubbed at urllib level; nothing leaves the machine.
"""
import json
from unittest.mock import patch

import pytest

from learning_engine.models import (
    AnthropicProvider, GeminiProvider, OllamaCluster, OllamaProvider,
)

REAL_GENERATE = {c: c.__dict__["generate"] for c in (OllamaProvider, OllamaCluster, GeminiProvider, AnthropicProvider)}


@pytest.mark.parametrize("cls", [OllamaProvider, OllamaCluster, GeminiProvider, AnthropicProvider])
def test_generate_accepts_the_generator_call(cls):
    import inspect
    inspect.signature(REAL_GENERATE[cls]).bind(object(), "prompt", system_instruction="sys", max_tokens=8192)


class _Resp:
    def __init__(self, body):
        self.body = body

    def read(self):
        return json.dumps(self.body).encode()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_ollama_passes_max_tokens_as_num_predict():
    sent = {}

    def fake_urlopen(req, timeout=None):
        sent.update(json.loads(req.data))
        return _Resp({"response": "A complete answer."})

    with patch("urllib.request.urlopen", fake_urlopen):
        provider = OllamaProvider(host="http://127.0.0.1:9", model="m")
        out = REAL_GENERATE[OllamaProvider](provider, "p", system_instruction="s", max_tokens=8192)
    assert out == "A complete answer."
    assert sent["options"]["num_predict"] == 8192


def test_ollama_cluster_forwards_max_tokens():
    cluster = OllamaCluster.__new__(OllamaCluster)
    cluster.preferred_model = "m"
    with patch.object(OllamaCluster, "select_node_for_model", return_value=("http://127.0.0.1:9", "m")), \
         patch.object(OllamaProvider, "generate", return_value="ok") as gen:
        assert REAL_GENERATE[OllamaCluster](cluster, "p", system_instruction="s", max_tokens=123) == "ok"
    assert gen.call_args.kwargs["max_tokens"] == 123


def test_every_chat_provider_can_stream():
    """/api/chat always streams; GeminiProvider (returned by get_chat_provider
    for a configured Gemini mentor model) had no generate_stream, so every
    answer was "'GeminiProvider' object has no attribute 'generate_stream'"."""
    from learning_engine.models import LLMProvider

    class OnlyGenerate(LLMProvider):
        def generate(self, prompt, system_instruction="", max_tokens=None):
            return f"answer to {prompt} ({max_tokens})"

    chunks = list(OnlyGenerate().generate_stream("q", system_instruction="s", max_tokens=2048))
    assert "".join(chunks) == "answer to q (2048)"
    for cls in (OllamaProvider, OllamaCluster, GeminiProvider, AnthropicProvider):
        assert callable(getattr(cls, "generate_stream", None)), cls.__name__
