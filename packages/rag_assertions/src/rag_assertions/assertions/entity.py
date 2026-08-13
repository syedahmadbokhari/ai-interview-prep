"""Entity existence assertions."""

from __future__ import annotations

import re
from collections.abc import Sequence

from rag_assertions.base import BaseAssertion
from rag_assertions.models import AssertionResult, EvidenceItem, ValidationContext

SAFE_REFUSAL_PATTERNS = (
    "no relevant information",
    "does not contain",
    "could not verify",
    "cannot verify",
    "not enough information",
    "not found",
)


class EntityExistsAssertion(BaseAssertion):
    """Validate that entity-like claims refer to known entities."""

    name = "entity_exists"

    def __init__(self, known_entities: Sequence[str] | None = None) -> None:
        self.known_entities = tuple(known_entities or ())

    def validate(
        self,
        answer: str,
        evidence: Sequence[EvidenceItem],
        context: ValidationContext,
    ) -> AssertionResult:
        known_entities = tuple(context.known_entities or self.known_entities)
        names = _known_entity_aliases(known_entities)
        mentioned = _mentioned_entities(answer, names)
        unknown = _unknown_entity_mentions(answer, context.question, names)

        if _is_safe_refusal(answer):
            return self.pass_result(
                "answer refuses or avoids unsupported entity claims",
                "The answer does not fabricate details for an unsupported entity.",
            )

        if unknown:
            return self.fail_result(
                unknown[0],
                f"Entity-like reference {unknown[0]!r} is not in the known entity registry.",
            )

        if mentioned:
            support = [
                item for item in evidence if item.entity in known_entities or item.project in known_entities
            ]
            entity = min(mentioned)
            return AssertionResult(
                assertion=self.name,
                passed=True,
                claim=", ".join(sorted(mentioned)),
                reason="Mentioned entity exists in the known entity registry.",
                evidence=support[:3],
                metadata={"entity": entity, "project": entity},
            )

        return self.pass_result(
            "no entity claim detected",
            "No entity-specific claim was detected.",
            skipped=True,
        )


class ProjectExistsAssertion(EntityExistsAssertion):
    """Compatibility assertion for applications that call entities projects."""

    name = "project_exists"


def _known_entity_aliases(known_entities: Sequence[str]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for entity in known_entities:
        aliases[entity.lower()] = entity
        compact = entity.replace("-", " ").lower()
        aliases[compact] = entity
        for token in compact.split():
            if len(token) >= 5:
                aliases[token] = entity
    return aliases


def _mentioned_entities(text: str, aliases: dict[str, str]) -> set[str]:
    lowered = text.lower()
    return {
        entity
        for alias, entity in aliases.items()
        if re.search(rf"\b{re.escape(alias)}\b", lowered)
    }


def _unknown_entity_mentions(answer: str, question: str, aliases: dict[str, str]) -> list[str]:
    candidates = []
    for text in (answer, question):
        for match in re.finditer(
            r"\b([A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]*){0,5})\s+(?:project|system|product|application)\b",
            text,
        ):
            phrase = match.group(1).strip()
            full = match.group(0).strip()
            if phrase.lower() not in aliases and not _phrase_contains_alias(phrase, aliases):
                candidates.append(full)
    return candidates


def _phrase_contains_alias(phrase: str, aliases: dict[str, str]) -> bool:
    lowered = phrase.lower()
    return any(re.search(rf"\b{re.escape(alias)}\b", lowered) for alias in aliases)


def _is_safe_refusal(answer: str) -> bool:
    lowered = answer.lower()
    return any(pattern in lowered for pattern in SAFE_REFUSAL_PATTERNS)
