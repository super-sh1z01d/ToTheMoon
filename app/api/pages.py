from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.templating import Jinja2Templates

from app.db.session import get_session
from app.models.token import TokenStatus
from app.repositories.token import list_tokens

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()


@router.get("/")
async def index(
    request: Request,
    status: TokenStatus | None = Query(default=TokenStatus.ACTIVE),
    session: AsyncSession = Depends(get_session),
):
    tokens = await list_tokens(session, status=status, limit=100)
    return templates.TemplateResponse("index.html", {"request": request, "tokens": tokens})
