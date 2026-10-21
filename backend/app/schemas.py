from pydantic import BaseModel, Field, field_validator

from . import config


class GenerationSettings(BaseModel):
    exaggeration: float = Field(0.5, ge=0.25, le=2.0)
    cfg_weight: float = Field(0.5, ge=0.0, le=1.0)
    temperature: float = Field(0.8, ge=0.05, le=2.0)
    repetition_penalty: float = Field(1.2, ge=1.0, le=2.0)
    seed: int = Field(42, ge=0, le=2**31 - 1)
    pause_ms: int = Field(400, ge=0, le=2000)


class GenerateRequest(BaseModel):
    text: str
    reference_id: str | None = None
    profile_id: str | None = None
    settings: GenerationSettings = GenerationSettings()

    @field_validator("text")
    @classmethod
    def _text(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Metin boş olamaz.")
        if len(v) > config.MAX_TEXT_CHARS:
            raise ValueError(f"Metin en fazla {config.MAX_TEXT_CHARS} karakter olabilir.")
        return v


class ProfileIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    reference_id: str | None = None
    settings: GenerationSettings = GenerationSettings()

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Profil adı boş olamaz.")
        return v


class SplitRequest(BaseModel):
    text: str = Field(max_length=config.MAX_TEXT_CHARS)
