from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Message:
    id: str
    text: str
    author: str


class MessageStorage(ABC):
    @abstractmethod
    async def list_messages(self) -> list[Message]: ...

    @abstractmethod
    async def create_message(self, text: str, author: str) -> Message: ...
