"""Background translation queue: one job at a time, progress, stop, dedupe."""
import threading
import time

import pytest
from fastapi.testclient import TestClient

import app.backend.main as be_main


class GatedProvider:
    """Translates each section only when the test opens the gate."""

    def __init__(self):
        self.gate = threading.Semaphore(0)
        self.calls = 0

    def generate(self, prompt):
        self.calls += 1
        assert self.gate.acquire(timeout=10), "test never released the section"
        return "# Přeložená sekce s dostatečně dlouhým textem pro kontrolu"


@pytest.fixture
def queue_client(monkeypatch):
    provider = GatedProvider()
    monkeypatch.setattr(be_main, "get_translation_provider", lambda **kw: (provider, "mock-model"))
    # A fresh queue per test (the worker task belongs to this client's event loop).
    monkeypatch.setattr(be_main, "TRANSLATIONS", be_main.TranslationQueue(
        get_provider=lambda **kw: be_main.get_translation_provider(**kw),
        executor=be_main.AI_EXECUTOR,
        cache_dir=be_main.translation_cache_dir,
    ))
    with TestClient(be_main.app) as client:
        yield client, provider
        be_main.TRANSLATIONS.stop_all()
        for _ in range(5):
            provider.gate.release()


def wait_for(client, job_id, pred, timeout=5.0):
    end = time.time() + timeout
    while time.time() < end:
        job = client.get(f"/api/translate/jobs/{job_id}").json()
        if pred(job):
            return job
        time.sleep(0.02)
    raise AssertionError(f"job never reached the expected state: {job}")


TEXT = "# One\nFirst section text.\n## Two\nSecond section text."


def test_job_reports_progress_and_result(queue_client):
    client, provider = queue_client
    job = client.post("/api/translate/jobs", json={"text": TEXT, "target_lang": "cs", "title": "Lesson 1"}).json()
    assert job["status"] in ("queued", "running")
    assert job["total"] == 2

    wait_for(client, job["id"], lambda j: j["status"] == "running" and provider.calls == 1)
    provider.gate.release()
    wait_for(client, job["id"], lambda j: j["done"] == 1)
    provider.gate.release()
    done = wait_for(client, job["id"], lambda j: j["status"] == "done")
    assert "Přeložená" in done["translated"]

    # Cached from now on: answered at once, no new job.
    again = client.post("/api/translate/jobs", json={"text": TEXT, "target_lang": "cs"}).json()
    assert again["status"] == "done" and again["cached"] is True


def test_runs_one_job_at_a_time_and_stops_queued_job(queue_client):
    client, provider = queue_client
    first = client.post("/api/translate/jobs", json={"text": TEXT, "target_lang": "cs"}).json()
    second = client.post("/api/translate/jobs", json={"text": TEXT, "target_lang": "de"}).json()
    wait_for(client, first["id"], lambda j: j["status"] == "running")
    queued = client.get(f"/api/translate/jobs/{second['id']}").json()
    assert queued["status"] == "queued" and queued["position"] == 1

    stopped = client.delete(f"/api/translate/jobs/{second['id']}").json()
    assert stopped["status"] == "stopped"
    statuses = {j["id"]: j["status"] for j in client.get("/api/translate/jobs").json()["jobs"]}
    assert statuses[second["id"]] == "stopped"


def test_stopping_running_job_starts_no_new_section(queue_client):
    client, provider = queue_client
    job = client.post("/api/translate/jobs", json={"text": TEXT, "target_lang": "cs"}).json()
    wait_for(client, job["id"], lambda j: j["status"] == "running" and provider.calls == 1)
    assert client.delete(f"/api/translate/jobs/{job['id']}").json()["stopping"] is True
    provider.gate.release()  # the section already sent to the model finishes
    wait_for(client, job["id"], lambda j: j["status"] == "stopped")
    assert provider.calls == 1


def test_same_lesson_and_language_reuses_running_job(queue_client):
    client, provider = queue_client
    a = client.post("/api/translate/jobs", json={"text": TEXT, "target_lang": "cs"}).json()
    b = client.post("/api/translate/jobs", json={"text": TEXT, "target_lang": "cs"}).json()
    assert a["id"] == b["id"]


def test_provider_unavailable_fails_job_with_reason(monkeypatch, queue_client):
    client, _ = queue_client
    def no_provider(**kw):
        raise RuntimeError("No Ollama nodes in the cluster are currently online.")
    monkeypatch.setattr(be_main, "get_translation_provider", no_provider)
    job = client.post("/api/translate/jobs", json={"text": TEXT, "target_lang": "es"}).json()
    failed = wait_for(client, job["id"], lambda j: j["status"] == "failed")
    assert "No AI model available" in failed["error"]


def test_stop_aborts_cancellable_model_call_mid_section(monkeypatch):
    """With a provider that supports it, Stop ends the section the model is working on."""
    from learning_engine.models import GenerationStopped

    class StreamingProvider:
        started = threading.Event()

        def generate_cancellable(self, prompt, should_stop):
            self.started.set()
            for _ in range(500):  # a long generation, checked between tokens
                if should_stop():
                    raise GenerationStopped()
                time.sleep(0.01)
            return "# Nikdy nedokončeno, protože test zastaví překlad"

    provider = StreamingProvider()
    monkeypatch.setattr(be_main, "get_translation_provider", lambda **kw: (provider, "mock-model"))
    monkeypatch.setattr(be_main, "TRANSLATIONS", be_main.TranslationQueue(
        get_provider=lambda **kw: be_main.get_translation_provider(**kw),
        executor=be_main.AI_EXECUTOR,
        cache_dir=be_main.translation_cache_dir,
    ))
    with TestClient(be_main.app) as client:
        job = client.post("/api/translate/jobs", json={"text": TEXT, "target_lang": "cs"}).json()
        assert provider.started.wait(5)
        t0 = time.time()
        client.delete(f"/api/translate/jobs/{job['id']}")
        wait_for(client, job["id"], lambda j: j["status"] == "stopped", timeout=2)
        assert time.time() - t0 < 2
