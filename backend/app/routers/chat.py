from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..agent.bot import run_chat
from ..database import get_db
from ..schemas import ChatIn, ChatOut

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatOut)
async def chat(data: ChatIn, db: Session = Depends(get_db)) -> ChatOut:
    return await run_chat(db, data.session_id, data.message)
