"""Evidence grounding: every fact must point at a verbatim span of its source text."""
from __future__ import annotations

import re
from collections.abc import Iterable

from .chem import normalize_text


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", normalize_text(text)).strip().lower()


def verify_evidence(evidence_span: str, source_text: str, normalized: bool = True) -> bool:
    """True if `evidence_span` occurs verbatim in `source_text`.

    With `normalized=True` (default) the comparison ignores whitespace, case and unicode
    sub/superscript or dash variants, which PDF extraction routinely alters. It never
    accepts paraphrases: the span's characters must appear in order and contiguously.
    """
    if not evidence_span or not source_text:
        return False
    if evidence_span in source_text:
        return True
    return normalized and _squash(evidence_span) in _squash(source_text)


def grounding_report(facts: Iterable[dict], source_lookup=None) -> dict:
    """Share of facts whose evidence span is found in their source text."""
    total = grounded = 0
    failures = []
    for fact in facts:
        source_text = source_lookup(fact) if source_lookup else fact.get("evidence_text", "")
        total += 1
        if verify_evidence(fact.get("evidence_span", ""), source_text or ""):
            grounded += 1
        else:
            failures.append({"id": fact.get("id"), "evidence_span": fact.get("evidence_span")})
    rate = grounded / total if total else 0.0
    return {"facts": total, "grounded": grounded, "grounding_rate": round(rate, 4),
            "meets_95pct_target": rate >= 0.95, "failures": failures[:50]}
