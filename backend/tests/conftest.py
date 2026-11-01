import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

BACKEND = Path(__file__).resolve().parent.parent
TEST_URL = os.environ.get("TEST_DATABASE_URL", "postgresql+psycopg://synapse:synapse@localhost:5432/synapse_test")


def alembic_config(url: str) -> Config:
    cfg = Config(str(BACKEND / "alembic.ini"))
    cfg.attributes["url"] = url
    return cfg


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_URL)
    try:
        eng.connect().close()
    except OperationalError:
        pytest.skip(f"PostgreSQL de test injoignable ({TEST_URL}) : lancer `docker compose up -d` dans backend/")
    with eng.begin() as c:
        c.execute(text("DROP SCHEMA public CASCADE"))
        c.execute(text("CREATE SCHEMA public"))
    command.upgrade(alembic_config(TEST_URL), "head")
    return eng


@pytest.fixture
def conn(engine):
    with engine.connect() as c:
        tx = c.begin()
        yield c
        tx.rollback()
