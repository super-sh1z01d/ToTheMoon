import os
from sqlmodel import create_engine, SQLModel

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tothemoon.db")

engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
