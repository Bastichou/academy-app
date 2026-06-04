import asyncio
import uuid
import redis.asyncio as aioredis
from .base import Message, MessageStorage


class RedisStorage(MessageStorage):
    INDEX_KEY = "messages:index"

    def __init__(self, client: aioredis.Redis) -> None:
        self._client = client

    async def list_messages(self) -> list[Message]:
        ids: list[bytes] = await self._client.lrange(self.INDEX_KEY, 0, -1)
        if not ids:
            return []
        msg_ids = [raw_id.decode() for raw_id in ids]
        results = await asyncio.gather(
            *[self._client.hgetall(f"message:{msg_id}") for msg_id in msg_ids]
        )
        return [
            Message(id=msg_id, text=data[b"text"].decode(), author=data[b"author"].decode())
            for msg_id, data in zip(msg_ids, results)
            if data
        ]

    async def create_message(self, text: str, author: str) -> Message:
        msg_id = str(uuid.uuid4())
        await self._client.hset(
            f"message:{msg_id}",
            mapping={"text": text, "author": author},
        )
        await self._client.rpush(self.INDEX_KEY, msg_id)
        return Message(id=msg_id, text=text, author=author)
