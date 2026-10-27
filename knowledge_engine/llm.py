"""LLM provider layer: the reasoning engine behind extraction, GraphRAG and hypotheses.

Provider order: Anthropic Claude (ANTHROPIC_API_KEY) -> OpenAI (OPENAI_API_KEY) -> offline.
Offline mode keeps the app, API and tests working with transparent rule-based fallbacks,
and every caller reports which mode produced its output.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

from .config import ROOT

try:
    from dotenv import load_dotenv
except ImportError:  # optional dependency
    def load_dotenv(*_args, **_kwargs):
        return False

load_dotenv(ROOT / ".env")

ANTHROPIC_MODEL = os.getenv("KE_ANTHROPIC_MODEL", "claude-opus-5-5")
OPENAI_MODEL = os.getenv("KE_OPENAI_MODEL", "gpt-4o-mini")
SYSTEM_PROMPT = ("You are a careful battery-materials scientist working on AHSC (asymmetric hybrid supercapacitor) "
                 "and LLZO (garnet solid electrolyte) research for African energy storage. Use only the evidence "
                 "you are given, cite fact ids, state uncertainty, and never invent DOIs or numerical values.")


@dataclass
class LLMResult:
    data: dict | None
    text: str
    mode: str  # "anthropic:<model>", "openai:<model>", "offline", or "<provider> error: ..."


def provider() -> str:
    if os.getenv("KE_LLM_PROVIDER") == "offline":
        return "offline"
    if os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN"):
        return "anthropic"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    return "offline"


def available() -> bool:
    return provider() != "offline"


def _parse_json(text: str) -> dict | None:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        match = re.search(r"\{.*\}", text or "", re.S)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
    return None


def _anthropic(prompt: str, schema: dict | None, system: str, effort: str) -> LLMResult:
    import anthropic

    client = anthropic.Anthropic()
    output_config: dict = {"effort": effort}
    if schema:
        output_config["format"] = {"type": "json_schema", "schema": schema}
    try:
        response = client.beta.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=16000,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_config=output_config,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",  # re-run on a fallback model if a request is declined
        )
    except anthropic.APIConnectionError as exc:
        return LLMResult(None, "", f"anthropic error: connection failed ({exc})")
    except anthropic.RateLimitError:
        return LLMResult(None, "", "anthropic error: rate limited, try again shortly")
    except anthropic.APIStatusError as exc:
        return LLMResult(None, "", f"anthropic error: HTTP {exc.status_code} {exc.message}")
    if response.stop_reason == "refusal":
        return LLMResult(None, "", "anthropic error: request declined")
    text = "".join(block.text for block in response.content if block.type == "text")
    return LLMResult(_parse_json(text) if schema else None, text, f"anthropic:{response.model}")


def _openai(prompt: str, schema: dict | None, system: str) -> LLMResult:
    from openai import OpenAI, OpenAIError

    try:
        kwargs = {"response_format": {"type": "json_object"}} if schema else {}
        content = prompt + (f"\n\nReturn only JSON matching this schema:\n{json.dumps(schema)}" if schema else "")
        response = OpenAI().chat.completions.create(
            model=OPENAI_MODEL, temperature=0,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": content}], **kwargs)
    except OpenAIError as exc:
        return LLMResult(None, "", f"openai error: {exc}")
    text = response.choices[0].message.content or ""
    return LLMResult(_parse_json(text) if schema else None, text, f"openai:{OPENAI_MODEL}")


def complete(prompt: str, schema: dict | None = None, system: str = SYSTEM_PROMPT, effort: str = "medium") -> LLMResult:
    """Run one LLM call. With `schema`, the result's `data` holds the parsed JSON object."""
    chosen = provider()
    if chosen == "anthropic":
        return _anthropic(prompt, schema, system, effort)
    if chosen == "openai":
        return _openai(prompt, schema, system)
    return LLMResult(None, "", "offline")
