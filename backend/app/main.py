import asyncio
from typing import List

from fastapi import FastAPI
from sqlmodel import Session, select

from .db import create_db_and_tables, engine
from .models.models import Token, ScoringParameter
from .services.ingestion import ingest_tokens
from .services.activation import activate_tokens
from .services.scoring import score_tokens

from .logging_config import setup_logging

app = FastAPI(title="ToTheMoon API")

@app.on_event("startup")
async def on_startup():
    setup_logging()
    create_db_and_tables()
    # Pre-populate default scoring parameters if they don't exist
    with Session(engine) as session:
        from .services.scoring import DEFAULT_WEIGHTS
        for name, value in DEFAULT_WEIGHTS.items():
            existing = session.exec(select(ScoringParameter).where(ScoringParameter.param_name == name)).first()
            if not existing:
                param = ScoringParameter(param_name=name, param_value=value, is_active=True)
                session.add(param)
        session.commit()

    asyncio.create_task(ingest_tokens())
    asyncio.create_task(activate_tokens())
    asyncio.create_task(score_tokens())

@app.get("/")
async def read_root():
    return {"message": "Welcome to the ToTheMoon API"}

@app.get("/api/tokens", response_model=List[Token])
def get_tokens():
    with Session(engine) as session:
        tokens = session.exec(select(Token).order_by(Token.last_smoothed_score.desc())).all()
        return tokens

@app.get("/api/parameters", response_model=List[ScoringParameter])
def get_parameters():
    with Session(engine) as session:
        params = session.exec(select(ScoringParameter)).all()
        return params

@app.post("/api/parameters", response_model=List[ScoringParameter])
def update_parameters(parameters: List[ScoringParameter]):
    with Session(engine) as session:
        for param_in in parameters:
            param_db = session.exec(
                select(ScoringParameter).where(ScoringParameter.param_name == param_in.param_name)
            ).first()
            if param_db:
                param_db.param_value = param_in.param_value
                session.add(param_db)
        session.commit()

        # Return the updated list
        updated_params = session.exec(select(ScoringParameter)).all()
        return updated_params

@app.get("/health")
def health_check():
    return {"status": "ok"}
