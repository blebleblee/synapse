"""
Lesson translation: the shared translation routine and a background queue.

The queue runs one translation at a time, so a local model is never asked to
translate several lessons at once. Jobs keep running when the reader moves to
another lesson; they can be stopped, and they all stop when the server exits
(the process ends and its open model connections close).
"""

import asyncio
import hashlib
import itertools
import re
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from learning_engine.models import GenerationStopped

LANGUAGE_NAMES = {
    "cs": "Czech (Čeština)",
    "de": "German (Deutsch)",
    "es": "Spanish (Español)",
    "ru": "Russian (Русский)",
    "en": "English",
}

# Finished jobs kept for the status list.
_FINISHED_KEEP = 20


def cache_file_for(cache_dir: Path, text: str, target_lang: str) -> Path:
    text_hash = hashlib.sha256((text + target_lang).encode("utf-8")).hexdigest()
    return cache_dir / f"{text_hash}_{target_lang}.md"


def read_cached(cache_dir: Path, text: str, target_lang: str) -> Optional[str]:
    f = cache_file_for(cache_dir, text, target_lang)
    return f.read_text(encoding="utf-8") if f.exists() else None


def split_sections(text: str) -> List[str]:
    """Chunks by # / ## headings so each request fits a local model's context."""
    return re.split(r'(?=\n#{1,2}\s+)', text)


def _mask(text: str) -> Tuple[str, list]:
    blocks: list = []

    def repl(m):
        token = f"___BLOCK_{len(blocks)}___"
        blocks.append(m.group(0))
        return token

    text = re.sub(r"```[\s\S]*?```", repl, text)
    text = re.sub(r"\$\$[\s\S]*?\$\$", repl, text)
    return text, blocks


def _unmask(text: str, blocks: list) -> str:
    for i, b in enumerate(blocks):
        text = text.replace(f"___BLOCK_{i}___", b)
    return text


def _prompt(masked_text: str, lang_name: str) -> str:
    return f"""You are an expert technical translator and polyglot philologist.
Translate the following technical curriculum text into {lang_name}.

CRITICAL INVARIANTS:
1. DO NOT translate or modify masked tokens like ___BLOCK_0___. Keep them exactly as is.
2. DO NOT translate Mermaid diagrams or code.
3. Translate all technical explanations and narrative prose with high fidelity and natural grammatical precision.
4. Output clean Markdown only with no preamble or wrapping.

Text to translate:
\"\"\"
{masked_text}
\"\"\""""


class TranslationStopped(Exception):
    pass


# Interactive AI requests (the mentor) in flight. Translations step aside for
# them: a local model answers one request at a time, so a mentor question
# would otherwise wait behind a whole translation section.
_interactive_count = 0
_interactive_lock = threading.Lock()


@contextmanager
def interactive_ai():
    global _interactive_count
    with _interactive_lock:
        _interactive_count += 1
    try:
        yield
    finally:
        with _interactive_lock:
            _interactive_count -= 1


def interactive_ai_active() -> bool:
    return _interactive_count > 0



async def translate_section(provider, executor, section: str, lang_name: str,
                            should_stop: Optional[Callable[[], bool]] = None) -> Tuple[str, bool, str]:
    """Returns (text, ok, error). On failure the English section comes back with ok=False.

    With should_stop, a provider that supports it (local Ollama) aborts the
    model's work mid-section; TranslationStopped is raised then.
    """
    if not section.strip():
        return section, True, ""
    masked, blocks = _mask(section)
    prompt = _prompt(masked, lang_name)
    cancellable = should_stop is not None and hasattr(provider, "generate_cancellable")
    try:
        loop = asyncio.get_running_loop()
        if cancellable:
            call = lambda: provider.generate_cancellable(prompt, should_stop)
        else:
            call = lambda: provider.generate(prompt)
        out = (await loop.run_in_executor(executor, call)).strip()
    except asyncio.CancelledError:
        raise
    except GenerationStopped:
        raise TranslationStopped()
    except Exception as e:
        return section, False, str(e)
    # Truncation guard: an answer under 20% of the source length is broken.
    if not out or len(out) < len(masked) * 0.2:
        return section, False, "the model's answer was empty or cut short"
    return _unmask(out, blocks), True, ""


class TranslationJob:
    def __init__(self, job_id: str, key: str, text: str, target_lang: str, title: str,
                 path: Optional[str], lesson_id: Optional[str], provider_args: Dict[str, Any]):
        self.id = job_id
        self.key = key
        self.text = text
        self.target_lang = target_lang
        self.title = title
        self.path = path
        self.lesson_id = lesson_id
        self.provider_args = provider_args
        self.status = "queued"  # queued | running | done | failed | stopped
        self.done = 0
        self.total = sum(1 for s in split_sections(text) if s.strip())
        self.result: Optional[str] = None
        self.fallback = False
        self.error: Optional[str] = None
        self.model: Optional[str] = None
        self.stop_requested = False
        self.paused = False  # waiting while the mentor uses the model
        self.created = time.time()
        self.finished: Optional[float] = None

    @property
    def active(self) -> bool:
        return self.status in ("queued", "running")

    def to_dict(self, position: Optional[int] = None, include_result: bool = False) -> Dict[str, Any]:
        d = {
            "id": self.id,
            "status": self.status,
            "target_lang": self.target_lang,
            "title": self.title,
            "path": self.path,
            "lesson_id": self.lesson_id,
            "done": self.done,
            "total": self.total,
            "model": self.model,
            "error": self.error,
            "fallback": self.fallback,
            "stopping": self.stop_requested and self.status == "running",
            "paused": self.paused and self.status == "running",
        }
        if position is not None:
            d["position"] = position
        if include_result and self.status == "done":
            d["translated"] = self.result
        return d


class TranslationQueue:
    """One worker, first in first out. Lives on the server's event loop."""

    def __init__(self, get_provider: Callable[..., Tuple[Any, str]], executor,
                 cache_dir: Callable[[], Path]):
        self._get_provider = get_provider
        self._executor = executor
        self._cache_dir = cache_dir
        self._jobs: Dict[str, TranslationJob] = {}
        self._pending: List[TranslationJob] = []
        self._wakeup: Optional[asyncio.Event] = None
        self._worker: Optional[asyncio.Task] = None
        self._ids = itertools.count(1)

    # -- public API -------------------------------------------------------
    def submit(self, text: str, target_lang: str, title: str = "", path: Optional[str] = None,
               lesson_id: Optional[str] = None, **provider_args) -> TranslationJob:
        key = hashlib.sha256((text + target_lang).encode("utf-8")).hexdigest()
        for job in self._jobs.values():
            if job.key == key and job.active:
                job.stop_requested = False
                return job
        job = TranslationJob(f"t{next(self._ids)}", key, text, target_lang, title or "Lesson",
                             path, lesson_id, provider_args)
        self._jobs[job.id] = job
        self._pending.append(job)
        self._ensure_worker()
        self._wakeup.set()
        self._prune()
        return job

    def get(self, job_id: str) -> Optional[TranslationJob]:
        return self._jobs.get(job_id)

    def stop(self, job_id: str) -> Optional[TranslationJob]:
        job = self._jobs.get(job_id)
        if not job or not job.active:
            return job
        if job.status == "queued":
            self._pending = [j for j in self._pending if j is not job]
            self._finish(job, "stopped")
        else:
            # The section being translated finishes in the model; no new one starts.
            job.stop_requested = True
        return job

    def stop_all(self) -> None:
        for job in list(self._jobs.values()):
            self.stop(job.id)

    def position(self, job: TranslationJob) -> Optional[int]:
        if job.status != "queued":
            return None
        return self._pending.index(job) + 1 if job in self._pending else None

    def describe(self, job: TranslationJob, include_result: bool = False) -> Dict[str, Any]:
        return job.to_dict(self.position(job), include_result)

    def list(self) -> List[Dict[str, Any]]:
        return [self.describe(j) for j in self._jobs.values()]

    async def shutdown(self) -> None:
        self.stop_all()
        if self._worker:
            self._worker.cancel()
            try:
                await self._worker
            except (asyncio.CancelledError, Exception):
                pass

    # -- worker -----------------------------------------------------------
    def _ensure_worker(self) -> None:
        if self._wakeup is None:
            self._wakeup = asyncio.Event()
        if self._worker is None or self._worker.done():
            self._worker = asyncio.get_running_loop().create_task(self._run())

    async def _run(self) -> None:
        while True:
            if not self._pending:
                self._wakeup.clear()
                await self._wakeup.wait()
                continue
            job = self._pending.pop(0)
            try:
                await self._translate(job)
            except asyncio.CancelledError:
                self._finish(job, "stopped")
                raise
            except Exception as e:  # never let one job kill the worker
                job.error = str(e)
                self._finish(job, "failed")

    async def _translate(self, job: TranslationJob) -> None:
        job.status = "running"
        try:
            provider, job.model = self._get_provider(**job.provider_args)
        except Exception as e:
            job.error = f"No AI model available: {e}"
            self._finish(job, "failed")
            return

        lang_name = LANGUAGE_NAMES.get(job.target_lang, job.target_lang)
        out: List[str] = []
        all_ok = True
        last_error = ""
        yield_or_stop = lambda: job.stop_requested or interactive_ai_active()
        for section in split_sections(job.text):
            while True:
                if job.stop_requested:
                    job.paused = False
                    self._finish(job, "stopped")
                    return
                # The mentor goes first: a local model answers one request at a time.
                if interactive_ai_active():
                    job.paused = True
                    await asyncio.sleep(0.3)
                    continue
                job.paused = False
                try:
                    text, ok, err = await translate_section(provider, self._executor, section, lang_name,
                                                            should_stop=yield_or_stop)
                except TranslationStopped:
                    continue  # stopped by the user, or paused for the mentor: re-check above
                break
            out.append(text)
            all_ok = all_ok and ok
            last_error = err or last_error
            if section.strip():
                job.done += 1
        if job.stop_requested:
            self._finish(job, "stopped")
            return

        final = "".join(out).strip()
        identical = final == job.text.strip()
        job.fallback = (not all_ok) or identical
        if not final:
            job.error = "The model returned no text."
            self._finish(job, "failed")
            return
        if all_ok and not identical:
            cache_dir = self._cache_dir()
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file_for(cache_dir, job.text, job.target_lang).write_text(final + "\n", encoding="utf-8")
        if not all_ok and identical:
            job.error = "The model could not translate this lesson" + (f": {last_error}" if last_error else ".")
            self._finish(job, "failed")
            return
        job.result = final
        self._finish(job, "done")

    def _finish(self, job: TranslationJob, status: str) -> None:
        job.status = status
        job.finished = time.time()
        self._prune()

    def _prune(self) -> None:
        finished = sorted((j for j in self._jobs.values() if not j.active), key=lambda j: j.finished or 0)
        for j in finished[:max(0, len(finished) - _FINISHED_KEEP)]:
            self._jobs.pop(j.id, None)
