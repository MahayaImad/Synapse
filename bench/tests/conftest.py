from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
NOMENCLATURE = ROOT / "app" / "assets" / "nomenclature" / "nomenclature.sqlite"


@pytest.fixture
def db():
    return NOMENCLATURE
