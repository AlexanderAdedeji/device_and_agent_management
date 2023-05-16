from os import environ

from backend.app.core.settings import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URI = settings.DATABASE_URI
DEBUG = settings.DEBUG


DATABASE_URI = environ.get("TEST_DB_URL") or str(DATABASE_URI)
engine = create_engine(DATABASE_URI, pool_pre_ping=True, echo=DEBUG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
