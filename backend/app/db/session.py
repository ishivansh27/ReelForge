"""
Database connection setup.

`SessionLocal` creates one database "conversation" per request.
`get_db` is a FastAPI dependency that opens a session, hands it to your
endpoint, and always closes it afterward -- even if the endpoint errors.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
