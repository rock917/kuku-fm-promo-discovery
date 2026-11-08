# =============================================================================
# llm_client.py — Swappable LLM Abstraction Layer
#
# Responsibilities:
#   - Provide a single interface for LLM calls regardless of provider
#   - Support: "gemini", "openai", "mock" (for testing without API key)
#   - Handle rate limiting, retries, and error recovery
#   - Cache responses to disk to avoid re-calling on reruns
#   - Never expose credentials in logs or outputs
#
# Provider is configured via config.yaml + .env (API key)
# To switch models: change config.yaml only — no source code changes needed.
# =============================================================================

from __future__ import annotations

import os
import json
import time
import hashlib
import logging
import textwrap
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Response cache
# ---------------------------------------------------------------------------

class ResponseCache:
    """
    File-based cache for LLM responses.
    Key: SHA256 hash of (provider + model + prompt).
    Value: JSON-serialised response dict.
    Prevents re-calling the API on reruns with the same input.
    """
    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key(self, provider: str, model: str, prompt: str) -> str:
        content = f"{provider}:{model}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get(self, provider: str, model: str, prompt: str) -> Optional[dict]:
        key = self._key(provider, model, prompt)
        path = self.cache_dir / f"{key}.json"
        if path.exists():
            try:
                return json.loads(path.read_text(encoding='utf-8'))
            except Exception:
                return None
        return None

    def set(self, provider: str, model: str, prompt: str, response: dict) -> None:
        key = self._key(provider, model, prompt)
        path = self.cache_dir / f"{key}.json"
        path.write_text(json.dumps(response, indent=2, ensure_ascii=False), encoding='utf-8')

    def size(self) -> int:
        return sum(1 for _ in self.cache_dir.glob("*.json"))


# ---------------------------------------------------------------------------
# Base LLM client interface
# ---------------------------------------------------------------------------

class LLMClient:
    """
    Abstract base for LLM provider clients.
    Subclasses implement _call_api().
    """
    def __init__(self, model: str, temperature: float = 0.2,
                 request_delay: float = 4.0, max_retries: int = 3,
                 cache: Optional[ResponseCache] = None):
        self.model = model
        self.temperature = temperature
        self.request_delay = request_delay
        self.max_retries = max_retries
        self.cache = cache
        self.provider = "base"
        self._last_call_time = 0.0

    def _rate_limit(self):
        """Enforce minimum delay between calls."""
        elapsed = time.time() - self._last_call_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)

    def call(self, prompt: str, expect_json: bool = True) -> dict:
        """
        Call the LLM with the given prompt.
        Returns a dict with keys: 'content' (str), 'raw' (any), 'cached' (bool), 'error' (str|None)
        """
        # Check cache
        if self.cache:
            cached = self.cache.get(self.provider, self.model, prompt)
            if cached is not None:
                logger.debug(f"Cache hit for prompt hash")
                return {**cached, "cached": True}

        # Rate limit
        self._rate_limit()

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                raw_text = self._call_api(prompt)
                self._last_call_time = time.time()

                result = {"content": raw_text, "raw": raw_text, "cached": False, "error": None}

                if expect_json:
                    parsed = self._extract_json(raw_text)
                    result["parsed"] = parsed

                # Cache successful response
                if self.cache:
                    self.cache.set(self.provider, self.model, prompt, result)

                return result

            except Exception as e:
                last_error = str(e)
                logger.warning(f"LLM call attempt {attempt}/{self.max_retries} failed: {e}")
                if attempt < self.max_retries:
                    time.sleep(self.request_delay * attempt)  # exponential backoff

        return {"content": "", "raw": None, "cached": False, "error": last_error, "parsed": None}

    def _call_api(self, prompt: str) -> str:
        raise NotImplementedError

    def _extract_json(self, text: str) -> Optional[dict]:
        """
        Extract JSON from LLM response text.
        Handles markdown code fences and raw JSON.
        """
        import re
        # Try to find JSON in ```json ... ``` block
        fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if fence_match:
            try:
                return json.loads(fence_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try raw JSON (find outermost { ... })
        brace_match = re.search(r'\{.*\}', text, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        logger.warning("Could not extract JSON from LLM response")
        return None


# ---------------------------------------------------------------------------
# Gemini client
# ---------------------------------------------------------------------------

class GeminiClient(LLMClient):
    """Google Gemini API client using google-generativeai SDK."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash", **kwargs):
        super().__init__(model=model, **kwargs)
        self.provider = "gemini"
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self._genai = genai
            self._model_instance = genai.GenerativeModel(
                model_name=model,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=4096,
                )
            )
            logger.info(f"Gemini client initialized: model={model}")
        except ImportError:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")

    def _call_api(self, prompt: str) -> str:
        response = self._model_instance.generate_content(prompt)
        return response.text


# ---------------------------------------------------------------------------
# OpenAI client (Supports native urllib.request or openai SDK)
# ---------------------------------------------------------------------------

class OpenAIClient(LLMClient):
    """OpenAI API client supporting standard urllib.request with fallback to openai SDK."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini", **kwargs):
        super().__init__(model=model, **kwargs)
        self.provider = "openai"
        self.api_key = api_key
        logger.info(f"OpenAI client initialized: model={model}")

    def _call_api(self, prompt: str) -> str:
        import urllib.request
        import urllib.error

        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert microdrama screenplay analyst. Keep reasoning brief and concise. Always respond in valid JSON format only."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": 350,
            "response_format": {"type": "json_object"},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "Kuku-Promo-Discovery/1.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                return res_data["choices"][0]["message"]["content"] or ""
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            logger.error(f"OpenAI API HTTP Error {e.code}: {err_body}")
            raise RuntimeError(f"OpenAI API Error ({e.code}): {err_body}")
        except Exception as e:
            logger.error(f"OpenAI API Request failed: {e}")
            raise


# ---------------------------------------------------------------------------
# Groq client (Ultra-fast, uses Groq OpenAI-compatible API)
# ---------------------------------------------------------------------------

class GroqClient(LLMClient):
    """
    Groq API client. Uses standard library urllib.request to call
    Groq's OpenAI-compatible completions endpoint without requiring external SDKs.
    """

    def __init__(self, api_key: str, model: str = "qwen/qwen3.8-27b", **kwargs):
        kwargs.setdefault("request_delay", 1.5)
        super().__init__(model=model, **kwargs)
        self.provider = "groq"
        self.api_key = api_key
        logger.info(f"Groq client initialized: model={model}")

    def _call_api(self, prompt: str) -> str:
        import urllib.request
        import urllib.error

        url = "https://api.groq.com/openai/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert microdrama screenplay analyst. Keep reasoning brief and concise. Always respond in valid JSON format only."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": 350,
            "response_format": {"type": "json_object"},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "Kuku-Promo-Discovery/1.0",
            },
            method="POST",
        )

        for attempt in range(8):
            try:
                with urllib.request.urlopen(req, timeout=40) as resp:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    return res_data["choices"][0]["message"]["content"] or ""
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace")
                logger.warning(f"Groq API HTTP Error {e.code} (attempt {attempt+1}/8): {err_body[:180]}")
                if e.code == 429:
                    import re
                    wait_sec = 8.0
                    min_match = re.search(r'try again in (?:(\d+)m)?([\d\.]+)s', err_body)
                    if min_match:
                        mins = float(min_match.group(1) or 0)
                        secs = float(min_match.group(2) or 0)
                        wait_sec = mins * 60 + secs + 2.0
                    elif "TPD" in err_body or "tokens per day" in err_body:
                        wait_sec = 60.0
                    logger.warning(f"Groq rate limit reached (429). Waiting {wait_sec:.1f}s before retry...")
                    time.sleep(wait_sec)
                    continue
                if attempt == 7:
                    raise RuntimeError(f"Groq API Error ({e.code}): {err_body}")
                time.sleep(3.0)
            except Exception as e:
                logger.error(f"Groq API Request failed: {e}")
                if attempt == 7:
                    raise
                time.sleep(3.0)
        raise RuntimeError("Groq API calls exhausted all retries.")


# ---------------------------------------------------------------------------
# Mock client (for testing without API key)
# ---------------------------------------------------------------------------

class MockLLMClient(LLMClient):
    """
    Mock LLM client for testing the pipeline without API calls.
    Returns deterministic placeholder scores based on simple heuristics.
    """

    def __init__(self, **kwargs):
        # Override request_delay to 0 for mock — no actual API calls, no throttling needed
        kwargs["request_delay"] = 0.0
        super().__init__(model="mock", **kwargs)
        self.provider = "mock"
        logger.info("Mock LLM client initialized (no API calls will be made)")

    def _call_api(self, prompt: str) -> str:
        # Extract episode number from prompt if possible
        import re
        ep_match = re.search(r'Episode (\d+)', prompt)
        ep_num = int(ep_match.group(1)) if ep_match else 0

        # Simple heuristic: episodes 1, 10, 32, 36 get higher scores
        high_drama_eps = {1, 2, 10, 18, 25, 32, 36, 42, 43}
        base_score = 7.5 if ep_num in high_drama_eps else 5.5

        mock_response = {
            "hook_strength": min(10, base_score + 1.0),
            "hook_text": "Opening moment creates immediate tension through visual betrayal.",
            "hook_reason": "MOCK: Determined by episode drama level heuristic.",
            "cliffhanger_strength": min(10, base_score + 0.5),
            "cliffhanger_text": "Scene ends without resolution, leaving viewer uncertain of outcome.",
            "cliffhanger_reason": "MOCK: Ending is unresolved based on heuristic assessment.",
            "standalone_clarity": min(10, base_score),
            "standalone_reason": "MOCK: Context is sufficiently self-explanatory for new viewers.",
            "emotional_impact": min(10, base_score + 0.5),
            "emotional_reason": "MOCK: High emotional stakes in this scene.",
            "explanation": f"MOCK ANALYSIS (Ep{ep_num}): This segment was selected by the mock client. "
                           f"Replace with real LLM for actual analysis.",
            "suggested_start_ts": None,
            "suggested_end_ts": None,
        }
        return json.dumps(mock_response)


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------

def create_llm_client(config: dict, cache_dir: Optional[Path] = None) -> LLMClient:
    """
    Create an LLM client from configuration.
    
    config keys:
      provider: "gemini" | "openai" | "mock"
      model: model name string
      temperature: float
      request_delay: float (seconds between calls)
      max_retries: int
    
    API keys read from environment variables:
      GEMINI_API_KEY  (for gemini)
      OPENAI_API_KEY  (for openai)
    """
    provider = config.get("provider", "mock").lower()
    model = config.get("model", "")
    temperature = float(config.get("temperature", 0.2))
    request_delay = float(config.get("request_delay", 4.0))
    max_retries = int(config.get("max_retries", 3))

    cache = ResponseCache(cache_dir) if cache_dir else None

    kwargs = dict(
        temperature=temperature,
        request_delay=request_delay,
        max_retries=max_retries,
        cache=cache,
    )

    if provider == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            logger.warning(
                "GEMINI_API_KEY not found in environment. "
                "Set it in .env or fall back to provider=mock."
            )
            raise ValueError(
                "GEMINI_API_KEY environment variable not set. "
                "Add it to your .env file or set provider=mock in config.yaml."
            )
        return GeminiClient(api_key=api_key, model=model or "gemini-1.5-flash", **kwargs)

    elif provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "").strip().strip('"\'')
        if api_key.upper().startswith("OPENAI_API_KEY="):
            api_key = api_key.split("=", 1)[1].strip().strip('"\'')
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Add it to your .env file or set provider=mock in config.yaml."
            )
        return OpenAIClient(api_key=api_key, model=model or "gpt-4o-mini", **kwargs)

    elif provider == "groq":
        api_key = os.environ.get("GROQ_API_KEY", "").strip().strip('"\'')
        if api_key.upper().startswith("GROQ_API_KEY="):
            api_key = api_key.split("=", 1)[1].strip().strip('"\'')
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY environment variable not set. "
                "Add it to your .env file or set provider=mock in config.yaml."
            )
        return GroqClient(api_key=api_key, model=model or "qwen/qwen3.8-27b", **kwargs)

    elif provider == "mock":
        return MockLLMClient(**kwargs)

    else:
        raise ValueError(f"Unknown LLM provider: '{provider}'. Choose: gemini | openai | groq | mock")


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    from pathlib import Path
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print("=" * 60)
    print("LLM CLIENT TEST")
    print("=" * 60)

    # Test mock client
    cache_dir = Path(r"e:\Kuku_FM_CASE_STUDY\outputs\cache")
    mock_client = MockLLMClient(cache=ResponseCache(cache_dir))

    test_prompt = "Analyze Episode 1: Scene shows betrayal at the altar."
    result = mock_client.call(test_prompt)
    print(f"\nMock client response:")
    print(f"  Cached: {result['cached']}")
    print(f"  Error:  {result['error']}")
    if result.get('parsed'):
        for k, v in result['parsed'].items():
            print(f"  {k}: {v}")

    # Second call should be cached
    result2 = mock_client.call(test_prompt)
    print(f"\nSecond call (should be cached): cached={result2['cached']}")

    # Test JSON extraction
    class _TestClient(LLMClient):
        def _call_api(self, prompt): return '{"key": "value", "score": 8.5}'
    tc = _TestClient("test-model")
    r = tc.call("test")
    print(f"\nJSON extraction test: parsed={r.get('parsed')}")

    # Test JSON in markdown fence
    class _TestClient2(LLMClient):
        def _call_api(self, prompt): return '```json\n{"key": "value2"}\n```'
    tc2 = _TestClient2("test-model")
    r2 = tc2.call("test")
    print(f"JSON fence extraction: parsed={r2.get('parsed')}")

    print(f"\nCache size after tests: {cache_dir}: {ResponseCache(cache_dir).size()} entries")
    print("\n✓ LLM client tests complete.")

