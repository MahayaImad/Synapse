from alembic import context
from sqlalchemy import create_engine

from synapse_admin.db import database_url, metadata

config = context.config
url = config.attributes.get("url") or database_url()


def run_migrations_online() -> None:
    connection = config.attributes.get("connection")
    if connection is not None:
        context.configure(connection=connection, target_metadata=metadata)
        with context.begin_transaction():
            context.run_migrations()
        return
    engine = create_engine(url)
    with engine.connect() as conn:
        context.configure(connection=conn, target_metadata=metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
