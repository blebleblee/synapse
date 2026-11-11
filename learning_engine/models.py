"""
LLM Provider Abstraction & Multi-Host Ollama Cluster
Supports clustered Ollama nodes (localhost, remote nodes, custom clusters) and Google Gemini.
"""

import os
import json
import urllib.request
import urllib.error
import itertools
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

DEFAULT_OLLAMA_HOSTS = [
    "http://127.0.0.1:11434",
    "http://studio.2464.cz:11434",
    "http://192.168.200.60:8080",
    "http://maxi.2464.cz:11434"
]

CLUSTER_HOST_SPECS: Dict[str, Dict[str, Any]] = {
    "http://127.0.0.1:11434": {
        "name": "localhost",
        "memory_tier": "large",
        "preferred_models": ["qwen2.5-coder:32b", "qwen2.5:32b", "deepseek-r1:32b", "llama3.1:latest"]
    },
    "http://studio.2464.cz:11434": {
        "name": "studio",
        "memory_tier": "large",
        "preferred_models": ["qwen2.5-coder:32b", "qwen3.6:35b-a3b-coding-mxfp8", "qwen3.5:35b-mlx", "gemma4:26b"]
    },
    "http://192.168.200.60:8080": {
        "name": "ai",
        "memory_tier": "24gb",
        "preferred_models": ["meta-llama-3.1-8b-instruct:latest", "gemma-4-12b-it-qat-q4_0:latest", "qwen3-8b:latest", "qwopus3.6-27b-v2-mtp-nvfp4:latest"]
    },
    "http://maxi.2464.cz:11434": {
        "name": "maxi",
        "memory_tier": "12gb",
        "preferred_models": ["llama3.1:8b", "gemma4:e4b", "qwen3:4b", "qwen2.5:3b"]
    }
}

def validate_generation_output(content: str) -> str:
    """
    Validates LLM output before persisting to disk.
    Rejects empty output and raw model runner metadata/loading payloads.
    """
    cleaned = (content or "").strip()
    if not cleaned:
        raise ValueError("LLM returned an empty response.")
    # Prevent raw runner status JSON from corrupting markdown files
    if cleaned.startswith("{") and ("\"done_reason\"" in cleaned or "\"created_at\"" in cleaned) and "\"done\":true" in cleaned.replace(" ", ""):
        raise ValueError(f"LLM returned raw model metadata instead of generated content: {cleaned[:120]}")
    return cleaned

CLUSTER_CONFIG_PATH = Path(__file__).resolve().parent.parent / ".synapse_cluster.json"

def get_configured_hosts() -> List[str]:
    # 1. Environment variable priority
    env_hosts = os.environ.get("OLLAMA_HOSTS")
    if env_hosts:
        return [h.strip().rstrip("/") for h in env_hosts.split(",") if h.strip()]
    # 2. Persistent workspace config
    if CLUSTER_CONFIG_PATH.exists():
        try:
            data = json.loads(CLUSTER_CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(data, list) and data:
                return [h.strip().rstrip("/") for h in data if h and isinstance(h, str)]
        except Exception:
            pass
    # 3. Default fallback cluster nodes
    return DEFAULT_OLLAMA_HOSTS

def save_configured_hosts(hosts: List[str]) -> List[str]:
    cleaned = [h.strip().rstrip("/") for h in hosts if h and isinstance(h, str) and h.strip()]
    if not cleaned:
        cleaned = DEFAULT_OLLAMA_HOSTS
    CLUSTER_CONFIG_PATH.write_text(json.dumps(cleaned, indent=2) + "\n", encoding="utf-8")
    return cleaned

class LLMProvider:
    def generate(self, prompt: str, system_instruction: str = "") -> str:
        raise NotImplementedError

class OllamaProvider(LLMProvider):
    def __init__(self, host: str = "http://localhost:11434", model: str = "qwen2.5-coder:32b"):
        self.host = host.rstrip("/")
        self.model = model

    @classmethod
    def is_available(cls, host: str = "http://localhost:11434") -> bool:
        # Check native Ollama /api/tags
        try:
            req = urllib.request.Request(f"{host.rstrip('/')}/api/tags", headers={"User-Agent": "LearningEngine"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass

        # Check LocalAI / OpenAI compatible /v1/models
        try:
            req = urllib.request.Request(f"{host.rstrip('/')}/v1/models", headers={"User-Agent": "LearningEngine"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    @classmethod
    def list_models(cls, host: str = "http://localhost:11434") -> List[str]:
        # 1. Native Ollama format
        try:
            req = urllib.request.Request(f"{host.rstrip('/')}/api/tags", headers={"User-Agent": "LearningEngine"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m["name"] for m in data.get("models", [])]
                if models:
                    return models
        except Exception:
            pass

        # 2. LocalAI / OpenAI /v1/models format
        try:
            req = urllib.request.Request(f"{host.rstrip('/')}/v1/models", headers={"User-Agent": "LearningEngine"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [m["id"] for m in data.get("data", [])]
        except Exception:
            return []

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

    def generate(self, prompt: str, system_instruction: str = "") -> str:
        # Try native Ollama API first
        ollama_url = f"{self.host}/api/generate"
        ollama_payload = {
            "model": self.model,
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
        v1_url = f"{self.host}/v1/chat/completions"
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        v1_payload = {
            "model": self.model,
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
            with urllib.request.urlopen(req, timeout=40) as resp:
                for line in resp:
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line.decode("utf-8"))
                        text = chunk.get("response", "")
                        if text:
                            yield text
                        if chunk.get("done", False):
                            break
                    except Exception:
                        continue
                return
        except Exception:
            pass

        # Fallback to non-streaming
        full_res = self.generate(prompt, system_instruction=system_instruction)
        yield full_res

class OllamaCluster(LLMProvider):
    """
    Manages a cluster of Ollama worker nodes across multiple machines,
    automatically routing requests to available nodes hosting the desired models.
    """
    def __init__(self, hosts: Optional[List[str]] = None, preferred_model: Optional[str] = None):
        self.hosts = hosts or get_configured_hosts()
        self.preferred_model = preferred_model
        self._host_cycle = itertools.cycle(self.hosts)

    def get_cluster_status(self) -> Dict[str, Any]:
        status = {}
        for h in self.hosts:
            up = OllamaProvider.is_available(h)
            models = OllamaProvider.list_models(h) if up else []
            status[h] = {
                "online": up,
                "models": models
            }
        return status

    def select_node_for_model(self, model: Optional[str] = None) -> Tuple[str, str]:
        """
        Finds the best (host, model) pair across the cluster.
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

    def get_parallel_workers(self) -> List[Tuple[str, str, OllamaProvider]]:
        """
        Returns active worker nodes with memory-tiered model allocations for parallel processing.
        Allocates large models to localhost and studio, 8B/12B models to ai (24GB),
        and compact 4B/8B models to maxi (12GB).
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
    def __init__(self, model: str = "gemini-2.5-flash", api_key: Optional[str] = None, project: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.project = project or os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")

        try:
            from google import genai
            if self.api_key:
                self.client = genai.Client(api_key=self.api_key)
            elif self.project:
                location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
                self.client = genai.Client(vertexai=True, project=self.project, location=location)
            else:
                self.client = None
        except ImportError:
            self.client = None

    def generate(self, prompt: str, system_instruction: str = "") -> str:
        if not self.client:
            raise RuntimeError("Google GenAI client not initialized. Set GEMINI_API_KEY or GOOGLE_CLOUD_PROJECT.")

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

def get_provider(provider_type: Optional[str] = None, model: Optional[str] = None, domain: Optional[str] = None) -> LLMProvider:
    """
    Selects provider or clustered Ollama nodes.
    Supports domain-specialized model routing (coding models for computing, reasoning models for math/physics).
    """
    cluster = OllamaCluster()
    cluster_status = cluster.get_cluster_status()
    any_ollama_up = any(data["online"] for data in cluster_status.values())

    if provider_type == "ollama" or (not provider_type and any_ollama_up):
        chosen_model = model
        if not chosen_model and domain:
            if domain == "computing_and_engineering":
                chosen_model = "qwen2.5-coder:32b"
            elif domain in ["formal_sciences", "natural_sciences"]:
                chosen_model = "deepseek-r1:32b"

        host, selected_model = cluster.select_node_for_model(chosen_model)
        return OllamaProvider(host=host, model=selected_model)

    chosen_model = model or "gemini-2.5-flash"
    return GeminiProvider(model=chosen_model)

def get_chat_provider(model: Optional[str] = None) -> Tuple[OllamaProvider, str]:
    """
    Returns a fast, low-latency model optimized for interactive Socratic mentoring.
    Prioritizes fast 7B/8B/4B models on localhost for instant token generation.
    """
    cluster = OllamaCluster()
    status = cluster.get_cluster_status()

    fast_models = [
        "qwen2.5-coder:7b",
        "llama3.1:8b",
        "meta-llama-3.1-8b-instruct:latest",
        "qwen3:4b",
        "qwen2.5:3b",
        "qwen2.5-coder:32b"
    ]

    if model:
        for host, h_data in status.items():
            if h_data.get("online") and model in h_data.get("models", []):
                return OllamaProvider(model=model, host=host), model

    local_key = "http://127.0.0.1:11434"
    local_data = status.get(local_key) or status.get("http://localhost:11434") or {}
    if local_data.get("online"):
        for fm in fast_models:
            if fm in local_data.get("models", []):
                return OllamaProvider(model=fm, host=local_key), fm

    for host, h_data in status.items():
        if h_data.get("online"):
            for fm in fast_models:
                if fm in h_data.get("models", []):
                    return OllamaProvider(model=fm, host=host), fm

    node, mod = cluster.select_best_node(model="llama3.1:8b")
    return OllamaProvider(model=mod, host=node), mod
