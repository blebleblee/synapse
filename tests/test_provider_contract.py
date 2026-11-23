"""
Every provider must accept the calls the app makes:
`generate(prompt, system_instruction=..., max_tokens=8192)` (lesson generator),
`generate_stream(..., max_tokens=2048)` (mentor chat) and, where present,
`generate_cancellable(prompt, should_stop)` (translation jobs).
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
# Resolved through the class hierarchy: providers without real streaming use
# LLMProvider.generate_stream.
REAL_STREAM = {c: getattr(c, "generate_stream") for c in (OllamaProvider, OllamaCluster, GeminiProvider, AnthropicProvider)}
REAL_CANCELLABLE = {c: c.__dict__["generate_cancellable"] for c in (OllamaProvider,) if "generate_cancellable" in c.__dict__}


@pytest.mark.parametrize("cls", [OllamaProvider, OllamaCluster, GeminiProvider, AnthropicProvider])
def test_generate_accepts_the_generator_call(cls):
    import inspect
    inspect.signature(REAL_GENERATE[cls]).bind(object(), "prompt", system_instruction="sys", max_tokens=8192)


@pytest.mark.parametrize("cls", [OllamaProvider, OllamaCluster, GeminiProvider, AnthropicProvider])
def test_generate_stream_accepts_the_chat_call(cls):
    """The mentor chat streams with `generate_stream(prompt,
    system_instruction=..., max_tokens=2048)` (app/backend/main.py)."""
    import inspect
    inspect.signature(REAL_STREAM[cls]).bind(object(), "prompt", system_instruction="sys", max_tokens=2048)


def test_generate_cancellable_accepts_the_translation_call():
    """Translation jobs call `generate_cancellable(prompt, should_stop)`
    (app/backend/translation_jobs.py)."""
    import inspect
    assert REAL_CANCELLABLE, "OllamaProvider.generate_cancellable is gone; translation jobs check for it"
    for fn in REAL_CANCELLABLE.values():
        inspect.signature(fn).bind(object(), "prompt", lambda: False)


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


def test_ollama_reply_keeps_text_before_the_first_heading():
    """Providers ran the lesson cleanup on every reply, which drops everything
    before the first heading. A mentor answer ("Good question! ... ## A hint")
    lost its opening paragraph in `synapse chat` and non-streaming /api/chat.
    Lesson-writing callers clean their own output."""
    reply = "Good question! What do you think a Pod is?\n\n## A hint\nContainers share a network namespace."
    with patch("urllib.request.urlopen", lambda req, timeout=None: _Resp({"response": reply})):
        provider = OllamaProvider(host="http://127.0.0.1:9", model="m")
        assert REAL_GENERATE[OllamaProvider](provider, "p", system_instruction="s") == reply


def test_translation_drops_a_model_preamble():
    """Translation relied on that provider cleanup to drop "Here is the
    translation:"; it now cleans the reply itself."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    from app.backend.translation_jobs import translate_section

    class P:
        def generate(self, prompt):
            return "Here is the translation:\n\n## Úvod\nToto je přeložený odstavec lekce."

    with ThreadPoolExecutor(1) as ex:
        out, ok, _ = asyncio.run(translate_section(P(), ex, "## Intro\nThis is the lesson paragraph.", "Czech"))
    assert ok and out.startswith("## Úvod")


def test_gemini_empty_reply_is_an_error_like_the_other_providers():
    """Gemini returned "" (e.g. a safety block); the mentor then showed and
    saved a blank answer instead of an error."""
    class _Models:
        def generate_content(self, **kw):
            return type("R", (), {"text": None})()

    provider = GeminiProvider.__new__(GeminiProvider)
    provider.model, provider.unavailable_reason = "g", None
    provider.client = type("C", (), {"models": _Models()})()
    pytest.importorskip("google.genai")
    with pytest.raises(ValueError, match="empty"):
        REAL_GENERATE[GeminiProvider](provider, "p", system_instruction="s")
