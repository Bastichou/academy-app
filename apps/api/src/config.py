from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_version: str = "0.1.0"
    azure_storage_connection_string: str = ""
    redis_url: str = ""

    @property
    def storage_backend(self) -> Literal["redis", "azure", "memory"]:
        if self.redis_url:
            return "redis"
        if self.azure_storage_connection_string:
            return "azure"
        return "memory"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
