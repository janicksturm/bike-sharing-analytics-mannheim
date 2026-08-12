import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://nextbike:nextbike@localhost:5432/nextbike"
)

engine = create_engine(DATABASE_URL, echo=True)

SessionFactory = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)
