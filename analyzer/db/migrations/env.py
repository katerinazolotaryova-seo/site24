import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make the `analyzer` package importable regardless of the working directory
# alembic is invoked from.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from analyzer.config import Settings  # noqa: E402
from analyzer.db import models  # noqa: E402,F401  (import registers models on Base.metadata)
from analyzer.db.base import Base  # noqa: E402

# A fresh instance (not the cached `analyzer.config.settings` singleton) so
# this picks up `ANALYZER_DATABASE_URL` as currently set in the environment
# at migration time — e.g. when a test overrides it via monkeypatch after
# `analyzer.config` was already imported elsewhere with a different value.
settings = Settings()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use the application's own settings for the DB URL instead of a hardcoded
# value in alembic.ini, so `ANALYZER_DATABASE_URL` controls migrations the
# same way it controls the running application.
config.set_main_option("sqlalchemy.url", settings.database_url)

# Model metadata, for `alembic revision --autogenerate`.
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
