from typing import Literal
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    mode: Literal['demo','live'] = Field('demo', alias='CALLPILOT_MODE')
    database_url: str = Field('sqlite:///outputs/callpilot.db',alias='CALLPILOT_DATABASE_URL')
    openai_model: str = Field('gpt-4o-mini',alias='CALLPILOT_OPENAI_MODEL')
    openai_api_key: SecretStr | None = Field(None,alias='OPENAI_API_KEY')
    allow_paid_live: bool = Field(False,alias='CALLPILOT_ALLOW_PAID_LIVE')
    max_requests: int = Field(16, ge=1, le=1000,alias='CALLPILOT_MAX_REQUESTS')
    timeout_seconds: float = Field(30,gt=0,le=120,alias='CALLPILOT_TIMEOUT_SECONDS')
    max_retries: int = Field(2,ge=0,le=3,alias='CALLPILOT_MAX_RETRIES')
    max_output_tokens: int = Field(4000,ge=100,le=8000,alias='CALLPILOT_MAX_OUTPUT_TOKENS')
    price_input_per_1m: float | None = Field(None,ge=0,alias='CALLPILOT_PRICE_INPUT_PER_1M')
    price_output_per_1m: float | None = Field(None,ge=0,alias='CALLPILOT_PRICE_OUTPUT_PER_1M')
    pricing_source_date: str | None = Field(None,alias='CALLPILOT_PRICING_SOURCE_DATE')
    blob_connection: SecretStr | None = Field(None,alias='AZURE_STORAGE_CONNECTION_STRING')
    blob_container: str = Field('callpilot-results',alias='AZURE_BLOB_CONTAINER')
    model_config=SettingsConfigDict(env_file='.env',extra='ignore',populate_by_name=True,env_ignore_empty=True)

def get_settings():
    return Settings()
