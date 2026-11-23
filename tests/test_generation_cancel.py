"""Stop interrupts a model call in progress during course generation.

Before: the generator called provider.generate(), which cannot be interrupted,
so Stop waited for every in-flight call (minutes on a large local model).
Loopback stub server only; no real provider.
"""
import json
import socket
import threading
import urllib.request
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import MagicMock

import pytest

from learning_engine import models as le_models
from learning_engine.generator import _call_model
from learning_engine.models import GenerationStopped, OllamaProvider

# Real functions, taken before conftest's autouse fixture replaces them.
REAL_CANCELLABLE = OllamaProvider.__dict__["generate_cancellable"]
_REAL_URLOPEN = urllib.request.urlopen
_REAL_CREATE_CONNECTION = socket.create_connection


class _Stub(BaseHTTPRequestHandler):
    status = 200
    payloads: list = []
    closed = threading.Event()

    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).payloads.append(body)
        if type(self).status != 200:
            self.send_response(type(self).status)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.end_headers()
        try:
            for i in range(200):  # ~20 s of tokens unless the client leaves
                self.wfile.write((json.dumps({"response": f"t{i} ", "done": False}) + "\n").encode())
                self.wfile.flush()
                time.sleep(0.1)
            self.wfile.write(b'{"response": "", "done": true}\n')
        except (BrokenPipeError, ConnectionResetError):
            type(self).closed.set()


def _loopback_only(monkeypatch):
    """Re-allow connections to 127.0.0.1 only (conftest blocks all network)."""
    def create_connection(address, *a, **k):
        assert address[0] == "127.0.0.1", f"non-loopback connection: {address}"
        return _REAL_CREATE_CONNECTION(address, *a, **k)

    def urlopen(req, *a, **k):
        url = req.full_url if hasattr(req, "full_url") else req
        assert url.startswith("http://127.0.0.1:"), f"non-loopback URL: {url}"
        return _REAL_URLOPEN(req, *a, **k)

    monkeypatch.setattr(socket, "create_connection", create_connection)
    monkeypatch.setattr(urllib.request, "urlopen", urlopen)


@pytest.fixture
def stub(monkeypatch):
    _loopback_only(monkeypatch)
    _Stub.status, _Stub.payloads = 200, []
    _Stub.closed = threading.Event()
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Stub)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def _provider(host):
    p = OllamaProvider.__new__(OllamaProvider)
    p.host, p.model = host, "stub-model"
    return p


def test_stop_interrupts_a_streaming_call_within_a_second(stub):
    stop = threading.Event()
    threading.Timer(0.5, stop.set).start()
    t0 = time.time()
    with pytest.raises(GenerationStopped):
        REAL_CANCELLABLE(_provider(stub), "prompt", stop.is_set, max_tokens=8192)
    assert time.time() - t0 < 2, "Stop must not wait for the full reply"
    assert _Stub.payloads[0]["options"]["num_predict"] == 8192
    assert _Stub.closed.wait(3), "the server must see the client leave (Ollama then aborts)"


def test_completed_stream_returns_the_text(stub, monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)  # the stub streams its 200 tokens at once
    out = REAL_CANCELLABLE(_provider(stub), "prompt", lambda: False)
    assert out.startswith("t0 t1 ") and out.rstrip().endswith("t199")
    assert "num_predict" not in _Stub.payloads[0]["options"]


def test_server_without_native_api_falls_back_to_generate(stub, monkeypatch):
    _Stub.status = 404
    p = _provider(stub)
    calls = []
    monkeypatch.setattr(OllamaProvider, "generate",
                        lambda self, prompt, system_instruction="", max_tokens=None: calls.append(max_tokens) or "## fallback")
    assert REAL_CANCELLABLE(p, "prompt", lambda: False, max_tokens=123) == "## fallback"
    assert calls == [123]


def test_stop_already_set_makes_no_request(stub):
    with pytest.raises(GenerationStopped):
        REAL_CANCELLABLE(_provider(stub), "prompt", lambda: True)
    assert _Stub.payloads == []


def test_call_model_uses_the_cancellable_path_when_the_class_has_it():
    seen = {}

    class Cancellable:
        def generate(self, *a, **k):
            raise AssertionError("must use generate_cancellable")

        def generate_cancellable(self, prompt, should_stop, system_instruction="", max_tokens=None):
            seen.update(prompt=prompt, stop=should_stop, system=system_instruction, max_tokens=max_tokens)
            return "ok"

    stop = lambda: False
    assert _call_model(Cancellable(), "p", "sys", stop, max_tokens=42) == "ok"
    assert seen == {"prompt": "p", "stop": stop, "system": "sys", "max_tokens": 42}


def test_call_model_keeps_generate_for_other_providers_and_mocks():
    m = MagicMock()
    m.generate.return_value = "text"
    assert _call_model(m, "p", "sys", lambda: False) == "text"
    m.generate.assert_called_once_with("p", system_instruction="sys")
    m.generate_cancellable.assert_not_called()


def test_call_model_raises_before_calling_when_stopped():
    m = MagicMock()
    with pytest.raises(GenerationStopped):
        _call_model(m, "p", "sys", lambda: True)
    m.generate.assert_not_called()
