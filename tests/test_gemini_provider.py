"""GeminiProvider against a fake google-genai client (no network).

Found with a live key (2026-11-23):
- the default gemini-2.5-flash answered 404 "no longer available to new users";
- Gemini 3 thinking counts against max_output_tokens: with 200 tokens the reply
  was "`set -" (finish reason MAX_TOKENS, 190 thinking tokens);
- gemini-3.5-flash-lite rejects thinking_budget=0 with 400 INVALID_ARGUMENT;
- mentor chat did not stream (one chunk from the base class).
"""
from types import SimpleNamespace

import pytest

from learning_engine.models import DEFAULT_GEMINI_MODEL, SHORT_REPLY_TOKENS, GeminiProvider

REAL_GENERATE = GeminiProvider.__dict__["generate"]
REAL_STREAM = GeminiProvider.__dict__["generate_stream"]


class FakeModels:
    def __init__(self, reject_no_thinking=False, chunks=("Hello ", "world")):
        self.configs, self.reject, self.chunks = [], reject_no_thinking, chunks

    def _check(self, config):
        self.configs.append(config)
        if self.reject and config.thinking_config is not None:
            raise RuntimeError("400 INVALID_ARGUMENT. Request contains an invalid argument.")

    def generate_content(self, model, contents, config):
        self._check(config)
        return SimpleNamespace(text="An answer.")

    def generate_content_stream(self, model, contents, config):
        self._check(config)
        return iter(SimpleNamespace(text=c) for c in self.chunks)


def _provider(models):
    p = GeminiProvider.__new__(GeminiProvider)
    p.model, p.unavailable_reason = DEFAULT_GEMINI_MODEL, None
    p.client = SimpleNamespace(models=models)
    return p


def test_default_model_is_a_current_one():
    assert DEFAULT_GEMINI_MODEL != "gemini-2.5-flash"
    assert GeminiProvider.__init__.__defaults__[0] == DEFAULT_GEMINI_MODEL


@pytest.mark.parametrize("budget", [200, SHORT_REPLY_TOKENS])
def test_short_calls_turn_thinking_off(budget):
    m = FakeModels()
    assert REAL_GENERATE(_provider(m), "q", max_tokens=budget) == "An answer."
    assert m.configs[0].thinking_config.thinking_budget == 0
    assert m.configs[0].max_output_tokens == budget


@pytest.mark.parametrize("budget", [None, 8192])
def test_long_calls_keep_the_models_thinking(budget):
    m = FakeModels()
    REAL_GENERATE(_provider(m), "q", max_tokens=budget)
    assert m.configs[0].thinking_config is None


def test_model_that_rejects_no_thinking_is_asked_again_without_it():
    m = FakeModels(reject_no_thinking=True)
    assert REAL_GENERATE(_provider(m), "q", max_tokens=200) == "An answer."
    assert [c.thinking_config is None for c in m.configs] == [False, True]


def test_other_errors_are_not_retried():
    class Down(FakeModels):
        def generate_content(self, model, contents, config):
            self.configs.append(config)
            raise RuntimeError("503 UNAVAILABLE")
    m = Down()
    with pytest.raises(RuntimeError, match="503"):
        REAL_GENERATE(_provider(m), "q", max_tokens=200)
    assert len(m.configs) == 1


def test_stream_yields_each_chunk():
    m = FakeModels(chunks=("One ", "two ", "three"))
    assert list(REAL_STREAM(_provider(m), "q", max_tokens=2048)) == ["One ", "two ", "three"]
    assert m.configs[0].thinking_config.thinking_budget == 0


def test_stream_falls_back_before_the_first_chunk():
    m = FakeModels(reject_no_thinking=True)
    assert "".join(REAL_STREAM(_provider(m), "q", max_tokens=2048)) == "Hello world"
    assert len(m.configs) == 2


def test_empty_stream_is_an_error():
    with pytest.raises(Exception):
        list(REAL_STREAM(_provider(FakeModels(chunks=("", ""))), "q", max_tokens=2048))
