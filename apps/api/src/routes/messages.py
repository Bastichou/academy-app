from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ..deps import get_storage
from ..storage.base import MessageStorage

router = APIRouter()


class MessageCreate(BaseModel):
    text: str
    author: str = "Anonyme"


@router.get("/messages")
async def list_messages(storage: MessageStorage = Depends(get_storage)):
    msgs = await storage.list_messages()
    return [{"id": m.id, "text": m.text, "author": m.author} for m in msgs]


@router.post("/messages", status_code=201)
async def create_message(
    body: MessageCreate,
    storage: MessageStorage = Depends(get_storage),
):
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Champ 'text' requis")
    msg = await storage.create_message(body.text, body.author)
    return {"id": msg.id, "text": msg.text, "author": msg.author}
