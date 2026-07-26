import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"
GOLDEN = ROOT / "golden"


@pytest.fixture(scope="session")
def golden_d1() -> dict:
    return json.loads((GOLDEN / "golden_d1.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def golden_forces() -> list[dict]:
    return json.loads((GOLDEN / "strip_forces_sample.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def mong_mdb_path() -> str:
    return str(FIXTURES / "MONG.mdb")
