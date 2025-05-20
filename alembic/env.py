import logging
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from db.db_routine import DBRoutine
from db.models import Base
from utils.config import DATABASE_PATH

# Set up logging
config = context.config
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

# Set database URL dynamically
config.set_main_option('sqlalchemy.url', f'sqlite:///{DATABASE_PATH}')

# Connectable (use DBRoutine's engine)
connectable = DBRoutine().engine

# Target metadata from models
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
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
    """Run migrations in 'online' mode."""
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()