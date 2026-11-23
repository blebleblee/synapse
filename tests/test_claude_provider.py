"""
Claude provider regressions:
- no retired model IDs as defaults (claude-3-5-sonnet-20241022 retired 2025-10-28);
- no sampling parameters (current Claude models reject temperature with HTTP 400);
- Haiku requested through a proxy is not silently remapped to Fable;
- a refusal raises instead of returning empty "successful" text;
- API keys saved from the Settings UI (camelCase keys) are used.
"""
import io
import json

import pytest

import learning_engine.models as models
from learning_engine.config_manager import save_settings

RETIRED = {"claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"}

# conftest replaces generate_stream on every test; keep the real one (captured
# at import, before fixtures run) for tests that drive it against a fake socket.
_REAL_GENERATE_STREAM = models.AnthropicProvider.generate_stream


class _FakeSSE(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _sse(events):
    return _FakeSSE("".join(f"data: {json.dumps(e)}\n\n" for e in events).encode())


@pytest.fixture
def captured(monkeypatch):
    calls = []

    def fake_urlopen(req, timeout=None):
        calls.append(json.loads(req.data.decode()))
        return calls_response[0]

    calls_response = [_sse([
        {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "hello"}},
        {"type": "message_delta", "delta": {"stop_reason": "end_turn"}},
    ])]
    monkeypatch.setattr(models.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(models.AnthropicProvider, "generate_stream", _REAL_GENERATE_STREAM)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    monkeypatch.delenv("VNAIPRO_BASE_URL", raising=False)
    return calls, calls_response


def test_request_has_no_sampling_parameters(captured):
    calls, _ = captured
    p = models.AnthropicProvider(model="claude-sonnet-5", base_url="https://api.anthropic.com")
    assert "".join(p.generate_stream("hi")) == "hello"
    body = calls[0]
    assert not {"temperature", "top_p", "top_k"} & set(body)
    assert body["model"] == "claude-sonnet-5"


def test_refusal_raises(captured):
    _, resp = captured
    resp[0] = _sse([{"type": "message_delta", "delta": {"stop_reason": "refusal"}}])
    p = models.AnthropicProvider(model="claude-sonnet-5", base_url="https://api.anthropic.com")
    with pytest.raises(RuntimeError, match="refusal"):
        list(p.generate_stream("hi"))


def test_haiku_through_proxy_is_not_mapped_to_fable(captured):
    p = models.AnthropicProvider(model="claude-haiku-5-5", base_url="https://proxy.example")
    assert p.model == "claude-haiku-5-5"
    assert "fable" not in p.model


def test_defaults_are_not_retired(captured):
    assert models.DEFAULT_CLAUDE_MODEL not in RETIRED
    p = models.get_provider(provider_type="anthropic")
    assert p.model not in RETIRED


def test_settings_ui_api_key_is_used(monkeypatch):
    for var in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "VNAIPRO_API_KEY", "ANTHROPIC_BASE_URL", "VNAIPRO_BASE_URL"):
        monkeypatch.delenv(var, raising=False)
    save_settings({"anthropicApiKey": "ui-key", "anthropicBaseUrl": "https://proxy.example"})
    p = models.AnthropicProvider(model="claude-sonnet-5")
    assert p.api_key == "ui-key"
    assert p.base_url == "https://proxy.example"


def test_user_agent_identifies_synapse(monkeypatch):
    seen = {}

    def fake_urlopen(req, timeout=None):
        seen.update({k.lower(): v for k, v in req.header_items()})
        return _sse([{"type": "message_delta", "delta": {"stop_reason": "end_turn"}}])

    monkeypatch.setattr(models.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(models.AnthropicProvider, "generate_stream", _REAL_GENERATE_STREAM)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.delenv("SYNAPSE_ANTHROPIC_USER_AGENT", raising=False)
    list(models.AnthropicProvider(model="claude-sonnet-5", base_url="https://api.anthropic.com").generate_stream("hi"))
    assert seen["user-agent"].startswith("Synapse-Workbench/")
    assert "claude-cli" not in seen["user-agent"]


@pytest.mark.parametrize("model", ["claude-sonnet-5-5", "claude-opus-4-5", "claude-fable-5-1"])
def test_proxy_keeps_full_model_ids(model):
    # A gateway's /v1/models lists exact IDs; rewriting them to one fixed name
    # per family sent requests for models the gateway does not have (404).
    p = models.AnthropicProvider(model=model, base_url="https://proxy.example")
    assert p.model == model


def test_proxy_still_maps_bare_family_names():
    p = models.AnthropicProvider(model="sonnet", base_url="https://proxy.example")
    assert p.model == "claude-sonnet-5"
