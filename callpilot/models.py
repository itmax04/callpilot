"""Shared input, model-output and persisted-result contracts."""
from datetime import date
from enum import Enum
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class Status(str, Enum):
    met = "met"
    not_met = "not_met"
    not_applicable = "not_applicable"
    insufficient_data = "insufficient_data"

class Utterance(StrictModel):
    id: str = Field(min_length=1)
    role: Literal["seller", "client"]
    text: str = Field(min_length=1)

    @field_validator("text")
    @classmethod
    def not_blank(cls, value):
        if not value.strip():
            raise ValueError("blank utterance")
        return value  # preserve whitespace and wording exactly

class Transcript(StrictModel):
    call_id: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    deal_id: str | None = None
    date: date
    language: Literal["ru", "uk"]
    recording_complete: bool = True
    utterances: list[Utterance] = Field(min_length=1)
    synthetic: bool

    @field_validator("utterances")
    @classmethod
    def unique_ids(cls, value):
        if len({u.id for u in value}) != len(value):
            raise ValueError("duplicate utterance ids")
        return value

class CriterionResult(StrictModel):
    criterion_id: int = Field(ge=1, le=7)
    status: Status
    explanation: str = Field(min_length=1)
    utterance_ids: list[str]
    quotes: list[str]

class ModelPayload(StrictModel):
    criteria: list[CriterionResult]

    @field_validator("criteria")
    @classmethod
    def seven(cls, value):
        if [c.criterion_id for c in value] != list(range(1, 8)):
            raise ValueError("criteria must contain ids 1..7 exactly once, in order")
        return value

class AnalysisResult(StrictModel):
    call_id: str
    prompt_version: str
    criteria: list[CriterionResult] = Field(default_factory=list)
    provider_status: Literal["demo", "success", "failed", "invalid_response", "budget_exhausted"]
    error_message: str | None = None  # safe error code only, never API response text
    model: str
    model_version: str | None = None
    prompt_hash: str
    input_hash: str
    latency_ms: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    attempts: int = 0
    cost_usd: float | None = None
    evidence_checks: list[dict] = Field(default_factory=list)
    review_required: bool = False

    @model_validator(mode="after")
    def valid_success(self):
        if self.provider_status in ("demo", "success"):
            ModelPayload(criteria=self.criteria)
        elif self.criteria:
            raise ValueError("Failed calls must not fabricate criterion statuses")
        return self
