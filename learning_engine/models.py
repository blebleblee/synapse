"""
LLM Provider Abstraction
Supports local Ollama models (offline, free) and Google Gemini (Cloud / API Key).
"""

import os
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List

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
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

    @classmethod
    def list_models(cls, host: str = "http://localhost:11434") -> List[str]:
        try:
            req = urllib.request.Request(f"{host.rstrip('/')}/api/tags", headers={"User-Agent": "LearningEngine"})
            with urllib.request.urlopen(req, timeout=2) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

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
            with urllib.request.urlopen(req, timeout=300) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                return res_json.get("response", "")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Ollama request failed: {e}")

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

def get_provider(provider_type: Optional[str] = None, model: Optional[str] = None) -> LLMProvider:
    """
    Selects provider automatically or explicitly:
    1. If provider_type is 'ollama': uses Ollama
    2. If provider_type is 'gemini': uses Gemini
    3. Auto: Checks if Ollama is running. If so, defaults to Ollama. Otherwise falls back to Gemini.
    """
    ollama_up = OllamaProvider.is_available()

    if provider_type == "ollama" or (not provider_type and ollama_up):
        models = OllamaProvider.list_models()
        chosen_model = model
        if not chosen_model:
            # Pick preferred model if available
            preferred = ["qwen2.5-coder:32b", "qwen3:4b", "llama3.1:8b", "qwen2.5:3b"]
            for pref in preferred:
                if pref in models:
                    chosen_model = pref
                    break
            if not chosen_model and models:
                chosen_model = models[0]
            if not chosen_model:
                chosen_model = "qwen2.5-coder:32b"

        return OllamaProvider(model=chosen_model)

    # Gemini fallback
    chosen_model = model or "gemini-2.5-flash"
    return GeminiProvider(model=chosen_model)
