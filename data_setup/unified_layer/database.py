# What this accomplishes:
# Production Flexibility: If you run this locally, it builds unified_layer.db. If you moves this to production and sets DATABASE_URL=postgresql://user:pass@host:5432/db,
# it points to Postgres without changing a single line of code.

# Concurrency Protection: The check_same_thread: False flag ensures that when multiple LangGraph agents query the SQLite database at the exact same time,
# it won't crash due to thread violations.
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from data_setup.unified_layer.models import Base

# Read the DATABASE_URL environment variable, defaulting to local SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///unified_layer.db")

# SQLite requires specific arguments for multi-threaded access (like LangGraph agents)
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

# Thread-safe session factory for database transactions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Binds the metadata and automatically creates all missing tables."""
    Base.metadata.create_all(bind=engine)
