import json
import requests
from typing import Optional

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mistral"


def query_mistral(prompt: str, system_prompt: Optional[str] = None, max_tokens: int = 1024) -> str:
    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
    payload = {
        "model": MODEL,
        "prompt": full_prompt,
        "stream": False,
        "options": {"num_predict": max_tokens, "temperature": 0.2}
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        return f"[LLM unavailable — fallback mode active: {str(e)}]"


def query_mistral_json(prompt: str, system_prompt: Optional[str] = None) -> dict:
    system = (system_prompt or "") + "\n\nRespond ONLY with valid JSON. No explanation, no markdown, no backticks."
    raw = query_mistral(prompt, system_prompt=system)
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
    except Exception:
        pass
    return {"error": "JSON parse failed", "raw": raw}


SYSTEM_PRE_IPO = """You are an expert capital markets infrastructure AI assistant for RaveMinds.
You analyse historical IPO surge data and predict system failure risks before an IPO event opens.
Be precise, actionable, and honest about confidence levels.
All analysis must reference specific historical precedents."""

SYSTEM_LIVE_SURGE = """You are a real-time operations AI assistant for RaveMinds monitoring an active IPO surge.
You must triage issues by urgency, distinguish surge-expected behaviour from genuine failures,
and provide clear plain-English recommendations ops teams can act on immediately.
Be concise — ops teams are under pressure."""

SYSTEM_POST_IPO = """You are a post-event analysis AI assistant for RaveMinds.
You audit prediction accuracy, extract lessons learned, and generate executive-ready summaries.
Be honest about what was predicted correctly and what was missed."""
