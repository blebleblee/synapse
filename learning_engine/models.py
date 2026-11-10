"""
LLM Provider Abstraction & Multi-Host Ollama Cluster
Supports clustered Ollama nodes (localhost, remote nodes, custom clusters) and Google Gemini.
"""

import os
import json
import urllib.request
import urllib.error
import itertools
from typing import Optional, Dict, Any, List, Tuple

DEFAULT_OLLAMA_HOSTS = [
    "http://localhost:11434"
]

def get_configured_hosts() -> List[str]:
    env_hosts = os.environ.get("OLLAMA_HOSTS")
    if env_hosts:
        return [h.strip().rstrip("/") for h in env_hosts.split(",") if h.strip()]
    return DEFAULT_OLLAMA_HOSTS

class LLMProvider:
    def generate(self, prompt: str, system_instruction: str = "") -> str:
        raise NotImplementedError

class OllamaProvider(LLMProvider):
    def __init__(self, host: str = "http://localhost:11434", model: str = "qwen2.5-coder:32b"):
        self.host = host.rstrip("/")
        self.model = model

    @classmethod
    def is_available(cls, host: str = "http://localhost:11434") -> bool:
        try:
            req = urllib.request.Request(f"{host.rstrip('/')}/api/tags", headers={"User-Agent": "LearningEngine"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    @classmethod
    def list_models(cls, host: str = "http://localhost:11434") -> List[str]:
        try:
            req = urllib.request.Request(f"{host.rstrip('/')}/api/tags", headers={"User-Agent": "LearningEngine"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [m["name"] for m in data.get("models", [])]
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
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_instruction,
            "stream": False,
            "options": {
                "temperature": 0.2
            }
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                return res_json.get("response", "")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Ollama request to {self.host} failed: {e}")

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
