import uuid
from .base import Message, MessageStorage


class InMemoryStorage(MessageStorage):
    def __init__(self) -> None:
        self._messages: list[Message] = []

    async def list_messages(self) -> list[Message]:
        return list(self._messages)

    async def create_message(self, text: str, author: str) -> Message:
        msg = Message(id=str(uuid.uuid4()), text=text, author=author)
        self._messages.append(msg)
        return msg
