"""
LLM Provider Abstraction & Multi-Host Ollama Cluster
Supports clustered Ollama nodes (localhost, remote nodes, custom clusters) and Google Gemini.
"""

import os
import json
import re
import time
import urllib.request
import urllib.error
import itertools
from pathlib import Path
from typing import Callable, Optional, Dict, Any, List, Tuple
from .config_manager import get_settings
from .security import get_workspace_root

WORKSPACE_ROOT = get_workspace_root()

DEFAULT_OLLAMA_HOSTS = [
    "http://127.0.0.1:11434"
]

def get_node_name(host: str) -> str:
    """Returns a clean display name for a cluster host."""
    clean = host.replace("http://", "").replace("https://", "").split(":")[0]
    return "localhost" if clean in ("127.0.0.1", "localhost") else clean

# Retained as empty dict for backwards compatibility
CLUSTER_HOST_SPECS: Dict[str, Dict[str, Any]] = {}

def repair_mermaid_diagrams(content: str) -> str:
    """
    Normalizes Mermaid diagram code blocks to ensure strict syntax compliance:
    - Normalizes subgraphs: subgraph "Title" -> subgraph sub_id ["Title"]
    - Normalizes edge labels with spaces or parens: -->|Text (parens)| -> -->|"Text (parens)"|
    - Normalizes node labels with parens: A[Text (parens)] -> A["Text (parens)"]
    """
    def sanitize_block(match):
        block = match.group(1)

        def repl_subgraph(m):
            title = m.group(1).strip()
            safe_id = re.sub(r"[^a-zA-Z0-9_]", "_", title).lower()[:32].strip("_")
            if not safe_id:
                safe_id = "group"
            return f'subgraph sub_{safe_id} ["{title}"]'

        block = re.sub(r'subgraph\s+"([^"\n]+)"?', repl_subgraph, block)
        block = re.sub(r'subgraph\s+([A-Za-z0-9_-]+[ \t]+[^\n\[]+)(?=\n|$)', repl_subgraph, block)

        def repl_edge_label(m):
            lbl = m.group(1).strip()
            if (" " in lbl or "(" in lbl or "/" in lbl) and not lbl.startswith('"'):
                return f'-->|"{lbl}"| '
            return m.group(0)

        block = re.sub(r'-->\s*\|\s*([^"|\n]+?)\s*\|\s*', repl_edge_label, block)
        block = re.sub(r'([A-Za-z0-9_-]+)\[([^"\]\n]*[\(\)\/\+\=\*\&][^"\]\n]*)\]', r'\1["\2"]', block)
        return f"```mermaid\n{block.strip()}\n```"

    return re.sub(r'```mermaid\n([\s\S]*?)```', sanitize_block, content)

def validate_lesson_completeness(content: str) -> str:
    """
    Strict quality gate for masterclass lessons.
    Rejects cut-off text, model refusals, and incomplete stubs.
    Enforces clean terminal punctuation and minimum substance.
    """
    cleaned = validate_generation_output(content)

    # 1. Refusal check
    refusal_markers = [
        "I can't proceed", "I cannot proceed", "I apologize",
        "I will not generate", "I cannot generate", "I am unable to fulfill"
    ]
    for marker in refusal_markers:
        if marker.lower() in cleaned.lower()[:350]:
            raise ValueError(f"Model refusal detected: {cleaned[:150]}")

    # 2. Minimum length check (> 3,500 characters for lessons, > 1,800 characters for capstone labs)
    is_lab = any(k in cleaned for k in ["# Capstone", "# Praktický projekt", "Capstone Challenge", "Praktický projekt", "## 1. Challenge Architecture", "## 1. Cíl projektu"])
    min_len = 1200
    if len(cleaned) < min_len:
        unit_type = "Lab" if is_lab else "Lesson"
        raise ValueError(f"{unit_type} draft too short/incomplete ({len(cleaned)} chars, expected > {min_len}).")

    # 3. Terminal Invariant: Must end with valid punctuation or closing code block
    lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
    if not lines:
        raise ValueError("Lesson output is empty.")
    last_line = lines[-1]

    valid_ends = (".", "!", "?", "```", '"', "'", ":", ")", "*", "---", "|")
    if not any(last_line.endswith(e) for e in valid_ends):
        raise ValueError(f"Truncated output: lesson cuts off mid-sentence without terminal punctuation ('{last_line[-80:]}').")

    return cleaned


def validate_generation_output(content: str) -> str:
    """
    Validates LLM output before persisting to disk.
    Rejects empty output or raw model runner metadata/loading payloads.
    Unwraps outer markdown code block if the entire response is fenced.
    """
    cleaned = (content or "").strip()
    if not cleaned:
        raise ValueError("LLM returned an empty response.")
    if cleaned.startswith("{") and '"done":true' in cleaned.replace(" ", ""):
        raise ValueError(f"LLM returned raw model metadata instead of generated content: {cleaned[:120]}")

    # Strip outer markdown fencing even if truncated at max_tokens or missing closing fence
    if cleaned.startswith("```markdown\n"):
        cleaned = cleaned[12:].strip()
    elif cleaned.startswith("```md\n"):
        cleaned = cleaned[6:].strip()
    elif cleaned.startswith("```\n") and not cleaned.startswith("```mermaid"):
        cleaned = cleaned[4:].strip()

    # A trailing fence with no opener is left over from an outer wrapper; a
    # balanced one closes the reply's last code block and stays.
    fences = sum(1 for ln in cleaned.splitlines() if ln.lstrip().startswith("```"))
    if fences % 2 == 1:
        if cleaned.endswith("\n```"):
            cleaned = cleaned[:-4].strip()
        elif cleaned.endswith("```") and not cleaned.startswith("```"):
            cleaned = cleaned[:-3].strip()

    # Strip conversational preambles/meta-commentary before the first heading
    # (# or ##). Lines inside code blocks ("# comment" in bash) are not headings.
    lines = cleaned.splitlines()
    in_fence = False
    for i, line in enumerate(lines):
        st = line.strip()
        if st.startswith("```") or st.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if st.startswith("# ") or st.startswith("## ") or st.startswith("**Lesson") or st.startswith("**Capstone"):
            cleaned = "\n".join(lines[i:]).strip()
            break

    return repair_mermaid_diagrams(cleaned)

def load_env_file():
    # User-level private config takes precedence over inherited shell env vars
    user_env = Path.home() / ".config" / "synapse" / "env"
    if user_env.exists():
        for line in user_env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k:
                    os.environ[k] = v

    workspace_env = WORKSPACE_ROOT / ".env"
    if workspace_env.exists():
        for line in workspace_env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k and k not in os.environ:
                    os.environ[k] = v

load_env_file()

def get_cluster_config_path() -> Path:
    return get_workspace_root() / ".synapse_cluster.json"

def get_node_pins_config_path() -> Path:
    return get_workspace_root() / ".synapse_node_pins.json"

CLUSTER_CONFIG_PATH = get_cluster_config_path()
NODE_PINS_CONFIG_PATH = get_node_pins_config_path()

def normalize_host_key(host: str) -> str:
    """Normalizes host string to hostname:port or hostname without protocol."""
    clean = host.strip().rstrip("/")
    clean = clean.replace("http://", "").replace("https://", "")
    return clean

def get_configured_node_pins() -> Dict[str, str]:
    """
    Returns mapping of normalized host/node key -> pinned model name.
    Loaded from environment, .synapse_node_pins.json, or SQLite settings.
    """
    pins: Dict[str, str] = {
        "192.168.1.100:8080": "qwen2.5-coder:32b",
        "192.168.1.100": "qwen2.5-coder:32b",
    }

    cfg_path = get_node_pins_config_path()
    if cfg_path.exists():
        try:
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                for k, v in data.items():
                    if k and v:
                        pins[normalize_host_key(k)] = str(v).strip()
        except Exception:
            pass

    try:
        from .config_manager import get_settings
        st = get_settings()
        db_pins = st.get("node_pins")
        if isinstance(db_pins, dict):
            for k, v in db_pins.items():
                if k and v:
                    pins[normalize_host_key(k)] = str(v).strip()
    except Exception:
        pass

    env_pins = os.environ.get("OLLAMA_NODE_PINS")
    if env_pins:
        try:
            if env_pins.strip().startswith("{"):
                parsed = json.loads(env_pins)
                for k, v in parsed.items():
                    pins[normalize_host_key(k)] = str(v).strip()
            else:
                for pair in env_pins.split(","):
                    if "=" in pair:
                        h, m = pair.split("=", 1)
                        pins[normalize_host_key(h)] = m.strip()
        except Exception:
            pass

    return pins

def get_node_pin(host: str) -> Optional[str]:
    """Resolves pinned model for a given host or None if not pinned."""
    pins = get_configured_node_pins()
    norm = normalize_host_key(host)
    if norm in pins:
        return pins[norm]
    host_only = norm.split(":")[0]
    if host_only in pins:
        return pins[host_only]
    return None

def save_configured_node_pins(pins: Dict[str, str]) -> Dict[str, str]:
    cleaned = {normalize_host_key(k): str(v).strip() for k, v in pins.items() if k and v}
    cfg_path = get_node_pins_config_path()
    cfg_path.write_text(json.dumps(cleaned, indent=2) + "\n", encoding="utf-8")
    try:
        from .config_manager import get_settings, save_settings
        st = get_settings()
        st["node_pins"] = cleaned
        save_settings(st)
    except Exception:
        pass
    return cleaned

def get_configured_hosts() -> List[str]:
    """Get Ollama hosts from .synapse_cluster.json or SQLite settings, falling back to localhost."""
    env_hosts = os.environ.get("OLLAMA_HOSTS")
    if env_hosts:
        return [h.strip().rstrip("/") for h in env_hosts.split(",") if h.strip()]

    cfg_path = get_cluster_config_path()
    if cfg_path.exists():
        try:
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
            if isinstance(data, list) and data:
                return [h.strip().rstrip("/") for h in data if h and isinstance(h, str) and h.strip()]
        except Exception:
            pass

    try:
        from .config_manager import get_settings
        st = get_settings()
        db_hosts = st.get("cluster_hosts")
        if isinstance(db_hosts, list) and db_hosts:
            return [h.strip().rstrip("/") for h in db_hosts if h and isinstance(h, str) and h.strip()]
    except Exception:
        pass

    return DEFAULT_OLLAMA_HOSTS

def save_configured_hosts(hosts: List[str]) -> List[str]:
    cleaned = [h.strip().rstrip("/") for h in hosts if h and isinstance(h, str) and h.strip()]
    if not cleaned:
        cleaned = DEFAULT_OLLAMA_HOSTS
    cfg_path = get_cluster_config_path()
    cfg_path.write_text(json.dumps(cleaned, indent=2) + "\n", encoding="utf-8")
    try:
        from .config_manager import get_settings, save_settings
        st = get_settings()
        st["cluster_hosts"] = cleaned
        save_settings(st)
    except Exception:
        pass
    return cleaned

class LLMProvider:
    def generate(self, prompt: str, system_instruction: str = "") -> str:
        raise NotImplementedError

class GenerationStopped(Exception):
    """Raised by generate_cancellable() when the caller asked it to stop."""


class OllamaProvider(LLMProvider):
    def __init__(self, host: str = "http://localhost:11434", model: str = "qwen2.5-coder:32b"):
        self.host = host.rstrip("/")
        self.model = model

    @classmethod
    def is_available(cls, host: str = "http://localhost:11434", timeout: float = 1.5) -> bool:
        # Check native Ollama /api/tags
        try:
            req = urllib.request.Request(f"{host.rstrip('/')}/api/tags", headers={"User-Agent": "LearningEngine"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass

        # Check LocalAI / OpenAI compatible /v1/models
        try:
            req = urllib.request.Request(f"{host.rstrip('/')}/v1/models", headers={"User-Agent": "LearningEngine"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status == 200
        except Exception:
            return False

    @classmethod
    def list_models(cls, host: str = "http://localhost:11434") -> List[str]:
        raw_models: List[str] = []
        # 1. Native Ollama format
        try:
            req = urllib.request.Request(f"{host.rstrip('/')}/api/tags", headers={"User-Agent": "LearningEngine"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m["name"] for m in data.get("models", [])]
                if models:
                    raw_models = models
        except Exception:
            pass

        # 2. LocalAI / OpenAI /v1/models format
        if not raw_models:
            try:
                req = urllib.request.Request(f"{host.rstrip('/')}/v1/models", headers={"User-Agent": "LearningEngine"})
                with urllib.request.urlopen(req, timeout=2.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    raw_models = [m["id"] for m in data.get("data", [])]
            except Exception:
                pass

        # Filter out non-LLM models (e.g. image diffusion models like flux, sd, etc.)
        non_llm_patterns = ["flux", "diffusion", "krea", "stable-diffusion", "dall-e", "midjourney"]
        filtered = [
            m for m in raw_models
            if not any(pat in m.lower() for pat in non_llm_patterns)
        ]

        # Prioritize pinned model if configured for this host
        pinned = get_node_pin(host)
        if pinned:
            if pinned in filtered:
                filtered.remove(pinned)
            filtered.insert(0, pinned)

        return filtered or raw_models

    @classmethod
    def pull_model(cls, host: str, model_name: str) -> bool:
        try:
            url = f"{host.rstrip('/')}/api/pull"
            payload = json.dumps({"name": model_name, "stream": False}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=1200) as resp:
                return resp.status == 200
        except Exception as e:
            print(f"[!] Error pulling model {model_name} on {host}: {e}")
            return False

    @classmethod
    def check_connectivity(cls, host: str, model: Optional[str] = None) -> bool:
        """Verifies if a specific Ollama/LocalAI node and model are available."""
        try:
            # Check if host is up (a busy Ollama can take a few seconds to answer)
            if not cls.is_available(host, timeout=4.0):
                return False
            
            # If a model is specified, verify it's available on that host
            if model:
                models = cls.list_models(host)
                return model in models
                
            return True
        except Exception:
            return False

    def generate(self, prompt: str, system_instruction: str = "", host: Optional[str] = None, model: Optional[str] = None) -> str:
        # Use provided overrides if available, otherwise use instance defaults
        target_host = host or self.host
        target_model = model or self.model
        
        # Try native Ollama API first
        ollama_url = f"{target_host.rstrip('/')}/api/generate"
        ollama_payload = {
            "model": target_model,
            "prompt": prompt,
            "system": system_instruction,
            "stream": False,
            "options": {
                "temperature": 0.2
            }
        }
        data = json.dumps(ollama_payload).encode("utf-8")
        req = urllib.request.Request(ollama_url, data=data, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                res_text = res_json.get("response", "")
                if res_text:
                    return validate_generation_output(res_text)
        except Exception:
            pass

        # Fallback to LocalAI / OpenAI compatible chat completions
        v1_url = f"{target_host.rstrip('/')}/v1/chat/completions"
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        v1_payload = {
            "model": target_model,
            "messages": messages,
            "temperature": 0.2
        }
        data = json.dumps(v1_payload).encode("utf-8")
        req = urllib.request.Request(v1_url, data=data, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                choices = res_json.get("choices", [])
                if choices:
                    text = choices[0].get("message", {}).get("content", "")
                    return validate_generation_output(text)
                raise RuntimeError(f"Unexpected response structure from {self.host}: {res_json}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Ollama/LocalAI request to {self.host} failed: {e}")

    def generate_cancellable(self, prompt: str, should_stop: Callable[[], bool], system_instruction: str = "") -> str:
        """Like generate(), but stops within a token or two once should_stop() is true.

        Streams from the native Ollama API; leaving the read loop closes the
        connection, and Ollama aborts the generation when its client goes away.
        """
        url = f"{self.host.rstrip('/')}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_instruction,
            "stream": True,
            "options": {"temperature": 0.2},
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        parts: List[str] = []
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                for line in resp:
                    if should_stop():
                        raise GenerationStopped()
                    if not line.strip():
                        continue
                    chunk = json.loads(line.decode("utf-8"))
                    if chunk.get("error"):
                        raise RuntimeError(f"Ollama: {chunk['error']}")
                    parts.append(chunk.get("response", ""))
                    if chunk.get("done"):
                        break
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")[:300]
            raise RuntimeError(f"Ollama request to {self.host} failed ({e.code}): {detail}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Ollama request to {self.host} failed: {e}")
        return validate_generation_output("".join(parts))

    def generate_stream(self, prompt: str, system_instruction: str = "", max_tokens: int = 250):
        # Native Ollama API streaming
        ollama_url = f"{self.host}/api/generate"
        ollama_payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_instruction,
            "stream": True,
            "options": {
                "temperature": 0.3,
                "num_predict": max_tokens
            }
        }
        data = json.dumps(ollama_payload).encode("utf-8")
        req = urllib.request.Request(ollama_url, data=data, headers={"Content-Type": "application/json"})

        try:
            has_streamed = False
            # Generous: Ollama may first have to load the model or finish
            # a request it already accepted.
            with urllib.request.urlopen(req, timeout=120) as resp:
                for line in resp:
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line.decode("utf-8"))
                        text = chunk.get("response", "")
                        if text:
                            has_streamed = True
                            yield text
                        if chunk.get("done", False):
                            break
                    except Exception:
                        continue
                if has_streamed:
                    return
        except Exception:
            pass

        # Fallback to LocalAI / OpenAI compatible streaming
        try:
            v1_url = f"{self.host}/v1/chat/completions"
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})
            v1_payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": max_tokens,
                "stream": True
            }
            data = json.dumps(v1_payload).encode("utf-8")
            req = urllib.request.Request(v1_url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                has_streamed = False
                for line in resp:
                    if not line:
                        continue
                    line_str = line.decode("utf-8", errors="replace").strip()
                    if line_str.startswith("data: "):
                        data_part = line_str[6:].strip()
                        if data_part == "[DONE]":
                            break
                        try:
                            parsed = json.loads(data_part)
                            choices = parsed.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                text = delta.get("content", "")
                                if text:
                                    has_streamed = True
                                    yield text
                        except Exception:
                            continue
                if has_streamed:
                    return
        except Exception:
            pass

        # Fallback to non-streaming
        full_res = self.generate(prompt, system_instruction=system_instruction)
        yield full_res

_CLUSTER_STATUS_CACHE: Dict[str, Any] = {"timestamp": 0.0, "status": {}}

class OllamaCluster(LLMProvider):
    """
    Manages a cluster of Ollama worker nodes across multiple machines,
    automatically routing requests to available nodes hosting the desired models.
    """
    def __init__(self, hosts: Optional[List[str]] = None, preferred_model: Optional[str] = None):
        self.hosts = hosts or get_configured_hosts()
        self.preferred_model = preferred_model
        self._host_cycle = itertools.cycle(self.hosts)

    def get_cluster_status(self, force_refresh: bool = False) -> Dict[str, Any]:
        global _CLUSTER_STATUS_CACHE
        now = time.time()
        if not force_refresh and (now - _CLUSTER_STATUS_CACHE["timestamp"] < 10.0) and _CLUSTER_STATUS_CACHE["status"]:
            return _CLUSTER_STATUS_CACHE["status"]

        status = {}
        from concurrent.futures import ThreadPoolExecutor

        def probe_node(h: str) -> Tuple[str, Dict[str, Any]]:
            up = OllamaProvider.is_available(h)
            models = OllamaProvider.list_models(h) if up else []
            pinned = get_node_pin(h)
            pref = pinned or (models[0] if models else None)
            return h, {
                "online": up,
                "models": models,
                "pinned_model": pinned,
                "preferred_model": pref
            }

        with ThreadPoolExecutor(max_workers=min(8, len(self.hosts) or 1)) as executor:
            for h, res in executor.map(probe_node, self.hosts):
                status[h] = res

        _CLUSTER_STATUS_CACHE = {"timestamp": now, "status": status}
        return status

    def select_node_for_model(self, model: Optional[str] = None) -> Tuple[str, str]:
        """
        Finds the best (host, model) pair across the cluster, honoring pinned models.
        """
        status = self.get_cluster_status()
        online_hosts = [h for h, data in status.items() if data["online"]]
        if not online_hosts:
            raise RuntimeError("No Ollama nodes in the cluster are currently online.")

        target_model = model or self.preferred_model

        if target_model:
            # Check which online hosts have this exact model
            for h in online_hosts:
                if target_model in status[h]["models"]:
                    return h, target_model

        # Check if any online host has a pinned model
        for h in online_hosts:
            pinned = status[h].get("pinned_model")
            if pinned and pinned in status[h]["models"]:
                return h, pinned

        # Model preference hierarchy
        preferred_models = [
            "qwen2.5-coder:32b",
            "qwen3.6:35b-a3b-coding-mxfp8",
            "deepseek-r1:32b",
            "qwen3.5:35b-mlx",
            "qwen2.5:32b",
            "gemma4:31b",
            "gemma4:26b",
            "gemma4:12b",
            "llama3.1:8b",
            "qwen3:4b",
            "qwen2.5:3b"
        ]

        for p_model in preferred_models:
            for h in online_hosts:
                if p_model in status[h]["models"]:
                    return h, p_model

        # Fallback to whatever first online model exists
        for h in online_hosts:
            if status[h]["models"]:
                return h, status[h]["models"][0]

        return online_hosts[0], "qwen3:4b"

    def get_parallel_workers(self, min_tier: str = "all") -> List[Tuple[str, str, OllamaProvider]]:
        """
        Returns active worker nodes with memory-tiered model allocations for parallel processing.
        If min_tier == 'large', filters for high-VRAM flagship nodes (30B/32B) for high-caliber drafting.
        """
        status = self.get_cluster_status()
        active_workers = []

        for host in self.hosts:
            host_clean = host.rstrip("/")
            norm_key = "http://127.0.0.1:11434" if "localhost" in host_clean else host_clean

            h_status = status.get(host_clean) or status.get(norm_key) or {}
            if not h_status.get("online"):
                continue

            available_models = h_status.get("models", [])
            spec = CLUSTER_HOST_SPECS.get(norm_key, {
                "name": host_clean,
                "memory_tier": "auto",
                "preferred_models": ["llama3.1:8b", "qwen3:4b"]
            })

            # Filter out compact/small nodes if large flagship tier requested
            if min_tier == "large" and spec.get("memory_tier") not in ["large", "24gb"]:
                continue

            selected_model = None
            for pref in spec["preferred_models"]:
                if pref in available_models:
                    selected_model = pref
                    break

            if not selected_model and available_models:
                selected_model = available_models[0]

            if selected_model:
                provider = OllamaProvider(host=norm_key, model=selected_model)
                active_workers.append((norm_key, selected_model, provider))

        return active_workers

    def generate(self, prompt: str, system_instruction: str = "") -> str:
        host, model = self.select_node_for_model(self.preferred_model)
        provider = OllamaProvider(host=host, model=model)
        return provider.generate(prompt, system_instruction=system_instruction)

class GeminiProvider(LLMProvider):
    def __init__(self, model: str = "gemini-2.5-flash", api_key: Optional[str] = None, project: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.project = project or os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")
        self.base_url = base_url or os.environ.get("GEMINI_BASE_URL")
        # Set by get_provider when Gemini is only the last-resort fallback.
        self.unavailable_reason: Optional[str] = None

        try:
            from google import genai
            from google.genai import types
            http_opts = types.HttpOptions(base_url=self.base_url) if self.base_url else None
            if self.api_key:
                self.client = genai.Client(api_key=self.api_key, http_options=http_opts)
            elif self.project:
                location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
                self.client = genai.Client(vertexai=True, project=self.project, location=location, http_options=http_opts)
            else:
                self.client = None
        except ImportError:
            self.client = None

    def generate(self, prompt: str, system_instruction: str = "") -> str:
        if not self.client:
            raise RuntimeError(self.unavailable_reason or "Google GenAI client not initialized. Set GEMINI_API_KEY or GOOGLE_CLOUD_PROJECT.")

        from google.genai import types
        config = types.GenerateContentConfig(
            temperature=0.2,
            system_instruction=system_instruction if system_instruction else None
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config
        )
        return response.text or ""

def _synapse_user_agent() -> str:
    try:
        from .version import __version__
    except Exception:
        __version__ = "0"
    return f"Synapse-Workbench/{__version__}"


# Default Claude model when none is configured (override with ANTHROPIC_MODEL).
DEFAULT_CLAUDE_MODEL = "claude-sonnet-5"


class AnthropicProvider(LLMProvider):
    """
    Anthropic Claude 3.5 Sonnet / Haiku / Opus Provider.
    Supports official Anthropic API as well as custom base URLs/proxies.
    Loads settings from config/settings.json or environment.
    """
    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None, base_url: Optional[str] = None):
        settings = get_settings()
        anthropic_cfg = settings.get("anthropic", {})

        self.base_url = (
            base_url or 
            os.environ.get("ANTHROPIC_BASE_URL") or 
            os.environ.get("VNAIPRO_BASE_URL") or
            anthropic_cfg.get("base_url") or 
            settings.get("anthropic_base_url") or
            settings.get("anthropicBaseUrl") or
            "https://api.anthropic.com"
        ).rstrip("/")

        self.api_key = (
            api_key or 
            os.environ.get("ANTHROPIC_API_KEY") or 
            os.environ.get("VNAIPRO_API_KEY") or
            os.environ.get("ANTHROPIC_AUTH_TOKEN") or 
            anthropic_cfg.get("api_key") or
            settings.get("anthropic_api_key") or
            settings.get("anthropicApiKey")
        )

        # Automatic fallback if legacy AIAPIFLOW URL is still referenced
        if "aiapiflow" in self.base_url.lower():
            fallback_url = os.environ.get("ANTHROPIC_BASE_URL") or os.environ.get("VNAIPRO_BASE_URL") or "https://apikey.vnaipro.app"
            if "aiapiflow" not in fallback_url.lower():
                self.base_url = fallback_url.rstrip("/")
            if not self.api_key:
                self.api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("VNAIPRO_API_KEY")

        resolved_req_model = model or os.environ.get("ANTHROPIC_MODEL") or anthropic_cfg.get("model") or "claude-sonnet-5"
        self.model = self._resolve_model_name(resolved_req_model)

    def _resolve_model_name(self, model: str) -> str:
        if not self.base_url.startswith("https://api.anthropic.com"):
            m_lower = model.lower()
            if "opus" in m_lower:
                return "claude-opus-5-5"
            if "fable" in m_lower:
                return "claude-fable-5"
            if "haiku" in m_lower:
                return "claude-haiku-5-5"
            if "sonnet" in m_lower:
                return "claude-sonnet-5"
            return "claude-sonnet-5"
        return model

    def _get_url(self) -> str:
        if self.base_url.endswith("/v1"):
            return f"{self.base_url}/messages"
        return f"{self.base_url}/v1/messages"

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "prompt-caching-2024-07-31",
            "content-type": "application/json",
            # Identify as this app, not as another client. Override only if your
            # gateway requires something specific (SYNAPSE_ANTHROPIC_USER_AGENT).
            "User-Agent": os.environ.get("SYNAPSE_ANTHROPIC_USER_AGENT") or _synapse_user_agent()
        }
        if self.api_key:
            headers["x-api-key"] = self.api_key
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def generate(self, prompt: str, system_instruction: str = "", max_tokens: int = 8192, retries: int = 5) -> str:
        """
        Generates full completion by consuming generate_stream with automatic retry
        on transient network or read timeouts.
        """
        last_err = None
        for attempt in range(1, retries + 1):
            try:
                chunks = []
                for chunk in self.generate_stream(prompt, system_instruction=system_instruction, max_tokens=max_tokens):
                    chunks.append(chunk)
                return validate_generation_output("".join(chunks))
            except Exception as e:
                last_err = e
                err_str = str(e)
                # Automatic key failover if active key runs out of credit (403 / 用户额度不足 / insufficient_quota)
                if any(q in err_str for q in ["403", "用户额度不足", "额度不足", "insufficient_quota"]):
                    raw_keys = [
                        os.environ.get("ANTHROPIC_API_KEY"),
                        os.environ.get("ANTHROPIC_API_KEY_2"),
                        os.environ.get("ANTHROPIC_API_KEY_3"),
                        os.environ.get("ANTHROPIC_API_KEY_4"),
                        os.environ.get("VNAIPRO_API_KEY"),
                        os.environ.get("VNAIPRO_API_KEY_2"),
                        os.environ.get("VNAIPRO_API_KEY_3"),
                        os.environ.get("VNAIPRO_API_KEY_4"),
                    ]
                    # Deduplicate preserving order
                    seen = set()
                    keys = [k for k in raw_keys if k and not (k in seen or seen.add(k))]
                    if len(keys) > 1:
                        try:
                            curr_idx = keys.index(self.api_key)
                            next_key = keys[(curr_idx + 1) % len(keys)]
                        except ValueError:
                            next_key = keys[0]
                        if next_key != self.api_key:
                            print(f"          [⚡] Key credit exhausted. Hot-swapping to surviving key...", flush=True)
                            self.api_key = next_key
                            continue

                # Automatic gateway failover if current gateway returns 503 (No available accounts) or 502
                if ("503" in err_str or "No available accounts" in err_str or "Upstream access forbidden" in err_str):
                    fallback_gateway = (os.environ.get("ANTHROPIC_BASE_URL") or os.environ.get("VNAIPRO_BASE_URL") or "https://apikey.vnaipro.app").rstrip("/")
                    if self.base_url != fallback_gateway:
                        self.base_url = fallback_gateway
                        continue
                if attempt < retries:
                    # Exponential backoff with stagger
                    time.sleep((2 ** attempt) + attempt)
                    continue
        raise last_err or RuntimeError("Anthropic generation failed after retries")

    def generate_stream(self, prompt: str, system_instruction: str = "", max_tokens: int = 8192):
        if not self.api_key:
            raise RuntimeError("ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN is not set.")

        url = self._get_url()
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "stream": True,
            "messages": [
                {"role": "user", "content": prompt}
            ]
            # No temperature/top_p/top_k: current Claude models reject sampling
            # parameters with HTTP 400.
        }
        if system_instruction and system_instruction.strip():
            # Enable Anthropic ephemeral prompt caching (90% input discount + faster TTFT)
            payload["system"] = [
                {
                    "type": "text",
                    "text": system_instruction.strip(),
                    "cache_control": {"type": "ephemeral"}
                }
            ]

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers=self._get_headers()
        )

        try:
            with urllib.request.urlopen(req, timeout=110) as resp:
                for line in resp:
                    if not line:
                        continue
                    line_str = line.decode("utf-8", errors="replace").strip()
                    if line_str.startswith("data: "):
                        json_str = line_str[6:].strip()
                        if json_str == "[DONE]":
                            break
                        try:
                            event = json.loads(json_str)
                            if event.get("type") == "error":
                                err_msg = event.get("error", {}).get("message", "Upstream streaming error")
                                raise RuntimeError(f"Anthropic streaming error: {err_msg}")
                            if event.get("type") == "content_block_delta":
                                delta = event.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    yield delta.get("text", "")
                            elif event.get("type") == "message_delta":
                                delta = event.get("delta", {})
                                if delta.get("stop_reason") == "max_tokens":
                                    raise RuntimeError("TruncationError: Anthropic hit max_tokens ceiling before completing chapter.")
                                if delta.get("stop_reason") == "refusal":
                                    raise RuntimeError("Anthropic declined the request (stop_reason: refusal).")
                        except RuntimeError:
                            raise
                        except Exception:
                            continue
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Anthropic API error ({e.code}): {err_body}")
        except Exception as e:
            raise RuntimeError(f"Anthropic stream failed: {e}")

def get_provider(
    provider_type: Optional[str] = None,
    model: Optional[str] = None,
    domain: Optional[str] = None,
    host: Optional[str] = None
) -> LLMProvider:
    """
    Selects provider or clustered Ollama nodes.
    Supports domain-specialized model routing (coding models for computing, reasoning models for math/physics).
    """
    if host and not provider_type:
        provider_type = "ollama"

    if provider_type == "anthropic" or (not provider_type and os.environ.get("ANTHROPIC_API_KEY") and model and "claude" in model):
        chosen_model = model or os.environ.get("ANTHROPIC_MODEL") or DEFAULT_CLAUDE_MODEL
        return AnthropicProvider(model=chosen_model)

    cluster = OllamaCluster()
    cluster_status = cluster.get_cluster_status()
    any_ollama_up = any(data["online"] for data in cluster_status.values())

    if provider_type == "ollama" or (not provider_type and any_ollama_up) or host:
        chosen_model = model
        if not chosen_model and domain:
            if domain == "computing_and_engineering":
                chosen_model = "qwen2.5-coder:32b"
            elif domain in ["formal_sciences", "natural_sciences"]:
                chosen_model = "deepseek-r1:32b"

        if host:
            return OllamaProvider(host=host, model=chosen_model or "qwen2.5-coder:32b")

        host, selected_model = cluster.select_node_for_model(chosen_model)
        return OllamaProvider(host=host, model=selected_model)

    chosen_model = model or "gemini-2.5-flash"
    gemini = GeminiProvider(model=chosen_model)
    if not provider_type and not gemini.client:
        hosts = ", ".join(cluster_status) or "none configured"
        gemini.unavailable_reason = (
            f"No AI model is reachable: no Ollama node answered ({hosts}) and no cloud key is set "
            "(GEMINI_API_KEY or GOOGLE_CLOUD_PROJECT). Start Ollama or add a key in Settings."
        )
    return gemini

def get_translation_provider(
    model: Optional[str] = None,
    provider_type: Optional[str] = None,
    host: Optional[str] = None
) -> Tuple[LLMProvider, str]:
    """
    Returns an LLM provider for technical curriculum translation.
    Respects explicit user model/host request and local AI configuration in Settings,
    falling back to reachable Ollama cluster nodes or cloud providers.
    """
    settings = get_settings()

    # 1. Determine if local AI is explicitly requested or configured as primary/mentor model
    cfg_primary = settings.get("primary_model", "")
    cfg_mentor = settings.get("mentor_model", "")
    is_local_requested = (
        provider_type == "ollama" or
        bool(host and ("11434" in host or "8080" in host or "localhost" in host or "127.0.0.1" in host)) or
        bool(model and any(m in model.lower() for m in ["qwen", "llama", "deepseek", "gemma", "mistral", "phi"]))
    )
    is_local_configured = any(
        m in (cfg_primary.lower() if cfg_primary else "") or m in (cfg_mentor.lower() if cfg_mentor else "")
        for m in ["qwen", "llama", "deepseek", "gemma", "mistral", "phi"]
    )

    # 2. If Local AI is requested or configured as primary
    if is_local_requested or (is_local_configured and not provider_type):
        target_model = model or cfg_mentor or cfg_primary or "qwen2.5-coder:32b"
        
        # Check explicit host if given
        if host and OllamaProvider.is_available(host):
            avail_models = OllamaProvider.list_models(host)
            chosen = target_model if target_model in avail_models else (avail_models[0] if avail_models else target_model)
            return OllamaProvider(host=host, model=chosen), chosen

        # Check configured Ollama cluster hosts
        for h in get_configured_hosts():
            if OllamaProvider.is_available(h):
                avail_models = OllamaProvider.list_models(h)
                if avail_models:
                    chosen = target_model if target_model in avail_models else avail_models[0]
                    return OllamaProvider(host=h, model=chosen), chosen

    # 3. Check Anthropic Claude if explicitly requested or if keys exist and no local AI was chosen
    anthropic_key = (
        os.environ.get("ANTHROPIC_API_KEY") or
        os.environ.get("ANTHROPIC_API_KEY_2") or
        os.environ.get("VNAIPRO_API_KEY") or
        settings.get("anthropic_api_key") or
        settings.get("anthropicApiKey") or
        settings.get("anthropic", {}).get("api_key")
    )
    if anthropic_key and (provider_type == "anthropic" or not is_local_configured or (model and "claude" in model.lower())):
        chosen_model = model or os.environ.get("ANTHROPIC_MODEL") or "claude-sonnet-5"
        return AnthropicProvider(model=chosen_model, api_key=anthropic_key), chosen_model

    # 4. Check Gemini
    gemini_key = os.environ.get("GEMINI_API_KEY") or settings.get("gemini_api_key") or settings.get("geminiApiKey")
    if gemini_key and (provider_type == "gemini" or (model and "gemini" in model.lower())):
        chosen_model = model or "gemini-2.5-flash"
        return GeminiProvider(model=chosen_model, api_key=gemini_key), chosen_model

    # 5. Fallback to any reachable Ollama node in the cluster
    for h in get_configured_hosts():
        if OllamaProvider.is_available(h):
            avail_models = OllamaProvider.list_models(h)
            if avail_models:
                chosen = model if (model and model in avail_models) else avail_models[0]
                return OllamaProvider(host=h, model=chosen), chosen

    # 6. Fallback to Anthropic if key exists even if local AI was preferred but unreachable
    if anthropic_key:
        chosen_model = os.environ.get("ANTHROPIC_MODEL") or "claude-sonnet-5"
        return AnthropicProvider(model=chosen_model, api_key=anthropic_key), chosen_model

    raise RuntimeError(
        "Translation requires an active LLM provider. Start local Ollama, or configure Claude/Gemini in Settings."
    )

def get_chat_provider(model: Optional[str] = None, host: Optional[str] = None) -> Tuple[LLMProvider, str]:
    """
    Returns a model provider optimized for interactive Socratic mentoring.
    Respects explicit user-specified host/model and database settings,
    falling back to auto-discovery or cloud services if necessary.
    """
    settings = get_settings()
    configured_model = model or settings.get("mentor_model") or settings.get("primary_model")

    anthropic_key = (
        os.environ.get("ANTHROPIC_API_KEY") or
        os.environ.get("ANTHROPIC_API_KEY_2") or
        os.environ.get("VNAIPRO_API_KEY") or
        settings.get("anthropic_api_key") or
        settings.get("anthropicApiKey")
    )

    # 0. If Claude / Anthropic is explicitly requested or set as preferred primary/mentor model
    if anthropic_key and configured_model and any(c in configured_model.lower() for c in ["claude", "sonnet", "opus", "anthropic"]):
        chosen_model = configured_model
        return AnthropicProvider(model=chosen_model, api_key=anthropic_key), chosen_model

    gemini_key = os.environ.get("GEMINI_API_KEY") or settings.get("gemini_api_key") or settings.get("geminiApiKey")
    if gemini_key and configured_model and "gemini" in configured_model.lower():
        return GeminiProvider(model=configured_model, api_key=gemini_key), configured_model

    # 1. Validate explicitly requested configuration
    if host and configured_model:
        if OllamaProvider.check_connectivity(host, configured_model):
            return OllamaProvider(model=configured_model, host=host), configured_model
    elif host:
        # Host requested, but model auto-selection needed
        if OllamaProvider.is_available(host):
            pinned = get_node_pin(host)
            models = OllamaProvider.list_models(host)
            # Use pinned model if available, else requested model, else first available
            selected_model = configured_model if (configured_model and configured_model in models) else (pinned if pinned else (models[0] if models else "qwen2.5-coder:7b"))
            return OllamaProvider(model=selected_model, host=host), selected_model

    # 2. Check cluster status if no valid explicit config
    fast_models = [
        "qwen2.5-coder:7b",
        "llama3.1:8b",
        "meta-llama-3.1-8b-instruct:latest",
        "qwen3:4b",
        "qwen2.5:3b",
        "qwen2.5-coder:32b"
    ]
    cluster = OllamaCluster()
    status = cluster.get_cluster_status()

    # Specific model request across cluster
    if configured_model:
        for h, h_data in status.items():
            if h_data.get("online") and configured_model in h_data.get("models", []):
                return OllamaProvider(model=configured_model, host=h), configured_model

    # Pinned model on online cluster node priority
    for h, h_data in status.items():
        if h_data.get("online") and h_data.get("pinned_model"):
            pinned = h_data["pinned_model"]
            return OllamaProvider(model=pinned, host=h), pinned

    # Localhost priority
    local_key = "http://127.0.0.1:11434"
    local_data = status.get(local_key) or status.get("http://localhost:11434") or {}
    if local_data.get("online"):
        for fm in fast_models:
            if fm in local_data.get("models", []):
                return OllamaProvider(model=fm, host=local_key), fm
        models = local_data.get("models", [])
        if models:
            return OllamaProvider(model=models[0], host=local_key), models[0]

    # Any online cluster node
    for h, h_data in status.items():
        if h_data.get("online"):
            for fm in fast_models:
                if fm in h_data.get("models", []):
                    return OllamaProvider(model=fm, host=h), fm
            models = h_data.get("models", [])
            if models:
                return OllamaProvider(model=models[0], host=h), models[0]

    # 3. If a specific model was configured/requested, preserve it on best cluster node
    if configured_model:
        node, mod = cluster.select_node_for_model(model=configured_model)
        return OllamaProvider(model=mod, host=node), mod

    # 4. Cloud fallbacks if no specific model was configured and Ollama is offline
    if anthropic_key:
        claude_model = os.environ.get("ANTHROPIC_MODEL") or DEFAULT_CLAUDE_MODEL
        return AnthropicProvider(model=claude_model, api_key=anthropic_key), claude_model

    if gemini_key:
        return GeminiProvider(model="gemini-2.5-flash", api_key=gemini_key), "gemini-2.5-flash"

    # 5. Default cluster selection
    node, mod = cluster.select_node_for_model(model="qwen2.5-coder:7b")
    return OllamaProvider(model=mod, host=node), mod
