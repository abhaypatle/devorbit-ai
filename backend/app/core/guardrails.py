import re
from dataclasses import dataclass
from enum import StrEnum

from app.core.config import get_settings


class GuardrailDecision(StrEnum):
    ALLOW = "allow"
    SANITIZE = "sanitize"
    BLOCK = "block"


@dataclass(frozen=True)
class GuardrailResult:
    decision: GuardrailDecision
    text: str
    reasons: tuple[str, ...] = ()
    redactions: int = 0


_INJECTION_PATTERNS = (
    re.compile(r"\bignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions?\b", re.I),
    re.compile(r"\bdisregard\s+(?:all\s+)?(?:system|developer|previous)\s+instructions?\b", re.I),
    re.compile(r"\b(?:reveal|print|show|dump)\s+(?:the\s+)?(?:hidden\s+)?system prompt\b", re.I),
    re.compile(r"<\s*/?\s*(?:system|developer)\s*>", re.I),
    re.compile(r"\b(?:override|bypass)\s+(?:the\s+)?(?:safety|guardrail|system)\b", re.I),
)
_AWS_ACCESS_KEY = re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")
_BEARER = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}")
_KNOWN_SECRET_TOKEN = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|xox[baprs]-[A-Za-z0-9-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")
_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")
_LABELED_SECRET = re.compile(
    r"(?i)\b((?:aws[_ -]?)?(?:api[_ -]?key|secret(?:[_ -]?access[_ -]?key)?|"
    r"password|token|access[_ -]?key))\b"
    r"(\s*[:=]\s*)[\"']?[A-Za-z0-9_./+=:-]{8,}[\"']?"
)
_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d ().-]{7,}\d)(?!\w)")
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def scan_ingress(text: str, *, max_length: int | None = None) -> GuardrailResult:
    configured_limit = max_length or get_settings().max_agent_input_chars
    if len(text) > configured_limit:
        return GuardrailResult(
            GuardrailDecision.BLOCK,
            "",
            (f"input_exceeds_{configured_limit}_characters",),
        )

    detected = any(pattern.search(text) for pattern in _INJECTION_PATTERNS)
    if detected and get_settings().guardrail_block_injection:
        return GuardrailResult(
            GuardrailDecision.BLOCK,
            "",
            ("prompt_injection_detected",),
        )

    cleaned = _CONTROL_CHARS.sub("", text)
    cleaned = cleaned.strip()
    if detected:
        return GuardrailResult(
            GuardrailDecision.SANITIZE,
            "[UNTRUSTED INSTRUCTION REMOVED]",
            ("prompt_injection_sanitized",),
        )
    if cleaned != text:
        return GuardrailResult(GuardrailDecision.SANITIZE, cleaned, ("control_characters_removed",))
    return GuardrailResult(GuardrailDecision.ALLOW, cleaned)


def scan_egress(text: str) -> GuardrailResult:
    redactions = 0
    reasons: list[str] = []

    def redact(pattern: re.Pattern[str], replacement: str, reason: str) -> None:
        nonlocal text, redactions
        text, count = pattern.subn(replacement, text)
        if count:
            redactions += count
            reasons.append(reason)

    redact(_AWS_ACCESS_KEY, "[REDACTED_AWS_ACCESS_KEY]", "aws_access_key_redacted")
    redact(_BEARER, "Bearer [REDACTED_TOKEN]", "bearer_token_redacted")
    redact(_KNOWN_SECRET_TOKEN, "[REDACTED_TOKEN]", "secret_token_redacted")
    redact(_JWT, "[REDACTED_JWT]", "jwt_redacted")
    redact(_LABELED_SECRET, r"\1\2[REDACTED_SECRET]", "labeled_secret_redacted")
    settings = get_settings()
    if settings.redact_emails:
        redact(_EMAIL, "[REDACTED_EMAIL]", "email_redacted")
    if settings.redact_phone_numbers:
        redact(_PHONE, "[REDACTED_PHONE]", "phone_number_redacted")
    decision = GuardrailDecision.SANITIZE if redactions else GuardrailDecision.ALLOW
    return GuardrailResult(decision, text, tuple(reasons), redactions)
