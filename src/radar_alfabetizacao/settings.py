"""Configuração por variáveis de ambiente (prefixo RADAR_); nenhum ID de projeto é fixo."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RADAR_", env_file=".env", extra="ignore")

    project_id: str
    bucket: str
    location: str = "US"
    bronze_dataset: str = "alfabetizacao_bronze"
    silver_dataset: str = "alfabetizacao_silver"
    gold_dataset: str = "alfabetizacao_gold"
    ops_dataset: str = "alfabetizacao_ops"
    pubsub_topic: str = "alfabetizacao-eventos"
    pubsub_subscription: str = "alfabetizacao-eventos-consumer"
    config_dir: Path = Path("config")
    sql_dir: Path = Path("sql")
    log_level: str = "INFO"

    @property
    def bronze(self) -> str:
        return f"{self.project_id}.{self.bronze_dataset}"

    @property
    def silver(self) -> str:
        return f"{self.project_id}.{self.silver_dataset}"

    @property
    def gold(self) -> str:
        return f"{self.project_id}.{self.gold_dataset}"

    @property
    def ops(self) -> str:
        return f"{self.project_id}.{self.ops_dataset}"
