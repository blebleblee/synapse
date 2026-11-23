"""Short Ollama calls ask thinking models not to think.

Ollama counts thinking tokens against num_predict: with default settings
gemma4:26b spent a 10-token budget thinking and replied "" (checked against
Ollama 0.40.17). Mentor chat streams with 2,048 tokens. No network: urlopen is
faked and only the request payload is inspected.
"""
import io
import json

import pytest

from learning_engine import models as le_models
from learning_engine.models import OllamaProvider, SHORT_REPLY_TOKENS

REAL_GENERATE = OllamaProvider.__dict__["generate"]
REAL_STREAM = OllamaProvider.__dict__["generate_stream"]
REAL_CANCELLABLE = OllamaProvider.__dict__["generate_cancellable"]


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


@pytest.fixture
def sent(monkeypatch):
    payloads = []

    def fake_urlopen(req, *a, **k):
        payloads.append(json.loads(req.data))
        if payloads[-1].get("stream"):
            return _Resp(b'{"response": "OK", "done": false}\n{"response": "", "done": true}\n')
        return _Resp(json.dumps({"response": "OK"}).encode())

    monkeypatch.setattr(le_models.urllib.request, "urlopen", fake_urlopen)
    return payloads


def _p():
    p = OllamaProvider.__new__(OllamaProvider)
    p.host, p.model = "http://127.0.0.1:11434", "gemma4:26b"
    return p


@pytest.mark.parametrize("budget", [10, 250, SHORT_REPLY_TOKENS])
def test_short_generate_turns_thinking_off(sent, budget):
    assert REAL_GENERATE(_p(), "q", max_tokens=budget) == "OK"
    assert sent[0]["think"] is False and sent[0]["options"]["num_predict"] == budget


@pytest.mark.parametrize("budget", [None, 8192])
def test_long_or_unbounded_generate_leaves_thinking_to_the_model(sent, budget):
    REAL_GENERATE(_p(), "q", max_tokens=budget)
    assert "think" not in sent[0]


def test_chat_stream_turns_thinking_off(sent):
    assert "".join(REAL_STREAM(_p(), "q", max_tokens=2048)) == "OK"
    assert sent[0]["think"] is False


def test_cancellable_follows_the_same_rule(sent):
    REAL_CANCELLABLE(_p(), "q", lambda: False, max_tokens=500)
    REAL_CANCELLABLE(_p(), "q", lambda: False, max_tokens=8192)
    REAL_CANCELLABLE(_p(), "q", lambda: False)
    assert [("think" in s) for s in sent] == [True, False, False]
    assert sent[0]["think"] is False
