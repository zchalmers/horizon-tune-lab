from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, field_validator
import re

# ── Input ────────────────────────────────────────────────────────────────────

INJECTION_PATTERNS = re.compile(
    r"ignore (previous|above|prior)|"
    r"\bsystem prompt\b|"
    r"(print|show|reveal|display|output|repeat|echo|tell me)(\s+\w+)?\s+(your |the )?(secret|password|token|api key|key|config|instruction|system|prompt|credential|path|internal|env\b|variable)|"
    r"(show|give|output|list|print|display)\s+(me\s+)?(your\s+)?(credential|password|token|secret|key|config)|"
    r"forget (previous|above|prior|all|everything)|"
    r"\bjailbreak\b|"
    r"disregard (previous|above|prior)|"
    r"act as (a |an )?(different|other|new|another)|"
    r"you are (now |)a\b|"
    r"pretend (to be|you are)|"
    r"execute (command|shell|script|code)|"
    r"run (command|shell|script|code|this)|"
    r"\bsudo\b|\beval\b|\bexec\b|\b__import__\b|"
    r"read (the )?(file|directory|path|folder|contents)|"
    r"(print|show|output|display|dump)\s+(the\s+)?(file|contents|directory)\b|"
    r"list (files|directories|dir )|"
    r"(what\s+is|tell me)\s+(your\s+)?(api\s*key|secret|password|token|system prompt)",
    re.IGNORECASE,
)

OFF_TOPIC_PATTERNS = re.compile(
    r"\b(crypto|bitcoin|stock|weather|recipe|lyrics|poem|essay|code|program|hack|"
    r"sql inject|xss|malware|exploit|vulnerability|jailbreak|"
    r"tell me a joke|write a story|help me with|how do I make money|"
    r"chatgpt|gpt-4|openai|llama|model api)\b",
    re.IGNORECASE,
)

FORZA_KEYWORDS = re.compile(
    r"\b(understeer|oversteer|wheelspin|spin|grip|traction|brake|drift|"
    r"suspension|spring|damper|arb|anti-roll|sway bar|alignment|camber|toe|caster|"
    r"differential|diff|gearing|ratio|aero|downforce|tire|tyre|pressure|"
    r"fwd|rwd|awd|s1|s2|a class|b class|x class|pi |"
    r"tune|tuning|setup|build|upgrade|car|forza|horizon|fh6|"
    r"throttle|acceleration|deceleration|corner|turn|exit|entry|"
    r"loose|tight|push|bounce|float|skitter|snap|slide)\b",
    re.IGNORECASE,
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=800)
    car: str | None = Field(None, max_length=80)
    drivetrain: str | None = Field(None, max_length=20)
    class_target: str | None = Field(None, max_length=20)
    discipline: Literal["road", "street", "dirt", "cross-country", "drag", "drift"] | None = None
    horsepower: int | None = Field(None, ge=1, le=3000)
    weight_lbs: int | None = Field(None, ge=500, le=10000)
    tires: str | None = Field(None, max_length=80)
    upgrades: list[str] = Field(default_factory=list, max_length=12)
    build_notes: str | None = Field(None, max_length=280)

    @field_validator("question")
    @classmethod
    def question_must_be_forza(cls, v: str) -> str:
        if INJECTION_PATTERNS.search(v):
            raise ValueError("off_topic")
        if not FORZA_KEYWORDS.search(v):
            if OFF_TOPIC_PATTERNS.search(v):
                raise ValueError("off_topic")
        return v.strip()

    @field_validator("car", "class_target", "tires", "build_notes", mode="before")
    @classmethod
    def strip_fields(cls, v: str | None) -> str | None:
        return v.strip() if v else None

    @field_validator("upgrades", mode="before")
    @classmethod
    def normalize_upgrades(cls, v: list[str] | str | None) -> list[str]:
        if not v:
            return []
        raw_items = v.split(",") if isinstance(v, str) else v
        items = []
        for item in raw_items:
            cleaned = str(item).strip()
            if cleaned:
                items.append(cleaned[:80])
        return items[:12]

    @field_validator("drivetrain", mode="before")
    @classmethod
    def normalize_drivetrain(cls, v: str | None) -> str | None:
        if not v:
            return None
        norm = v.strip().upper()
        allowed = {"AWD", "RWD", "FWD", "4WD", "4X4"}
        if norm not in allowed:
            raise ValueError("invalid_drivetrain")
        return "AWD" if norm in {"4WD", "4X4"} else norm


class EvidenceItem(BaseModel):
    type: Literal["effect", "interaction", "baseline", "car", "build", "recommendation"]
    title: str
    summary: str


class SafetyInfo(BaseModel):
    mode: Literal["deterministic", "llm_disabled"] = "deterministic"
    refused: bool = False
    refusal_reason: str | None = None


class AskResponse(BaseModel):
    answer: str
    likely_cause: str
    try_in_order: list[str]
    watch_for: list[str]
    evidence: list[EvidenceItem]
    safety: SafetyInfo


class RefusalResponse(BaseModel):
    answer: str
    safety: SafetyInfo


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def strip_content(cls, v: str) -> str:
        return v.strip()


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1, max_length=12)
    car: str | None = Field(None, max_length=80)
    drivetrain: str | None = Field(None, max_length=20)
    class_target: str | None = Field(None, max_length=20)
    discipline: Literal["road", "street", "dirt", "cross-country", "drag", "drift"] | None = None
    horsepower: int | None = Field(None, ge=1, le=3000)
    weight_lbs: int | None = Field(None, ge=500, le=10000)
    tires: str | None = Field(None, max_length=80)
    upgrades: list[str] = Field(default_factory=list, max_length=12)
    build_notes: str | None = Field(None, max_length=280)

    @field_validator("car", "class_target", "tires", "build_notes", mode="before")
    @classmethod
    def strip_context_fields(cls, v: str | None) -> str | None:
        return v.strip() if v else None

    @field_validator("upgrades", mode="before")
    @classmethod
    def normalize_chat_upgrades(cls, v: list[str] | str | None) -> list[str]:
        return AskRequest.normalize_upgrades(v)

    @field_validator("drivetrain", mode="before")
    @classmethod
    def normalize_chat_drivetrain(cls, v: str | None) -> str | None:
        return AskRequest.normalize_drivetrain(v)

    def latest_user_message(self) -> str:
        for message in reversed(self.messages):
            if message.role == "user":
                return message.content
        raise ValueError("no_user_message")

    def recent_user_context(self) -> str:
        user_messages = [m.content for m in self.messages if m.role == "user"]
        if not user_messages:
            raise ValueError("no_user_message")
        recent = user_messages[-3:]
        if len(recent) == 1:
            return recent[0]
        combined = "\n".join(f"User said: {message}" for message in recent)
        return combined[-800:]

    def to_ask_request(self) -> AskRequest:
        return AskRequest(
            question=self.recent_user_context(),
            car=self.car,
            drivetrain=self.drivetrain,
            class_target=self.class_target,
            discipline=self.discipline,
            horsepower=self.horsepower,
            weight_lbs=self.weight_lbs,
            tires=self.tires,
            upgrades=self.upgrades,
            build_notes=self.build_notes,
        )


class ChatResponse(BaseModel):
    message: ChatMessage
    answer: AskResponse | RefusalResponse


class CarResult(BaseModel):
    id: int
    make: str
    car_name: str
    full_name: str
    year: int | None
    car_type: str | None
    class_letter: str | None
    pi: int | None


class CarSearchResponse(BaseModel):
    results: list[CarResult]
    total: int


class HealthResponse(BaseModel):
    status: str
    db: str
