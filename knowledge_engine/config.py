"""Repository paths shared by every engine module."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
REPORTS_DIR = ROOT / "reports"
LITERATURE_DIR = DATA_DIR / "literature"

AHSC_CSV = ROOT / "ahsc_cleaned (1).csv"
LLZO_CSV = ROOT / "llzo_cleaned (1).csv"
MINERALS_CSV = DATA_DIR / "mineral_resources.csv"
AFRICA_SUPPLY_CSV = DATA_DIR / "africa_element_supply.csv"
RECORD_SOURCES_CSV = DATA_DIR / "record_sources.csv"
KNOWLEDGE_SEED = ROOT / "knowledge_base" / "literature_seed.md"

FACTS_JSONL = DATA_DIR / "thesis_facts.jsonl"
LITERATURE_FACTS_JSONL = DATA_DIR / "literature_facts.jsonl"
LITERATURE_METADATA = LITERATURE_DIR / "metadata.json"
GRAPHML_PATH = DATA_DIR / "knowledge_graph.graphml"
SCHEMA_PATH = ROOT / "schema.json"
CHROMA_DIR = ROOT / "chroma_db"
