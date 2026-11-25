import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Ensure parent directory for SQLite DB file exists
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite:///"):
    db_path_str = db_url.replace("sqlite:///", "")
    # Handle absolute posix paths like sqlite:////data/app.db
    if db_path_str.startswith("/"):
        db_path = Path(db_path_str)
    else:
        db_path = Path(db_path_str).resolve()
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
