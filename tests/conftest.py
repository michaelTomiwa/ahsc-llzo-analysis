import os
import sys
from pathlib import Path

# Deterministic, network-free tests: offline LLM mode and the scikit-learn search backend.
os.environ["KE_LLM_PROVIDER"] = "offline"
os.environ["KE_SEARCH_BACKEND"] = "lsa"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def engine():
    from knowledge_engine.graph_rag import Engine

    return Engine()
