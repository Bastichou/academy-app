import asyncio
import uuid
from azure.data.tables import TableServiceClient
from .base import Message, MessageStorage
from ..config import get_settings

TABLE_NAME = "messages"


class AzureTableStorage(MessageStorage):
    def __init__(self) -> None:
        conn_str = get_settings().azure_storage_connection_string.strip()
        if not conn_str:
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING is not set or empty")
        service = TableServiceClient.from_connection_string(conn_str)
        service.create_table_if_not_exists(TABLE_NAME)
        self._table = service.get_table_client(TABLE_NAME)

    async def list_messages(self) -> list[Message]:
        entities = await asyncio.to_thread(list, self._table.list_entities())
        return [
            Message(id=e["RowKey"], text=e["text"], author=e["author"])
            for e in entities
        ]

    async def create_message(self, text: str, author: str) -> Message:
        msg_id = str(uuid.uuid4())
        entity = {
            "PartitionKey": "messages",
            "RowKey": msg_id,
            "text": text,
            "author": author,
        }
        await asyncio.to_thread(self._table.create_entity, entity)
        return Message(id=msg_id, text=text, author=author)
