"""Local-first RAG utilities for the Streamlit prototype."""
from __future__ import annotations

import os
import re
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # Dashboard still works in local retrieval mode without optional packages.
    def load_dotenv(*_args, **_kwargs):
        return False

ROOT = Path(__file__).resolve().parent
KNOWLEDGE_PATH = ROOT / "knowledge_base" / "literature_seed.md"


def chunks(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n(?=# )", text) if part.strip()]


def retrieve(question: str, limit: int = 3) -> list[str]:
    """Transparent keyword retrieval; works without API credentials."""
    terms = {term.lower() for term in re.findall(r"[a-zA-Z]{3,}", question)}
    passages = chunks(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
    ranked = sorted(passages, key=lambda p: sum(term in p.lower() for term in terms), reverse=True)
    return [passage for passage in ranked[:limit] if passage]


def answer(question: str) -> tuple[str, list[str], str]:
    context = retrieve(question)
    load_dotenv(ROOT / ".env")
    if not os.getenv("OPENAI_API_KEY"):
        joined = "\n\n".join(context)
        return ("Local retrieval mode is active. Add `OPENAI_API_KEY` to `.env` to enable LangChain LLM synthesis. "
                "The most relevant source passages are shown below.\n\n" + joined, context, "local retrieval")
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI
        model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        joined_context = "\n\n".join(context)
        prompt = ("Answer only from the supplied research context. State uncertainty and do not give investment or medical advice. "
                  f"Context:\n{joined_context}\n\nQuestion: {question}")
        response = model.invoke([SystemMessage(content="You are a careful battery-materials research assistant."), HumanMessage(content=prompt)])
        return response.content, context, "LangChain + OpenAI"
    except Exception as exc:
        return (f"LLM request could not run ({exc}). Showing local retrieval instead.\n\n" + "\n\n".join(context),
                context, "local fallback")
