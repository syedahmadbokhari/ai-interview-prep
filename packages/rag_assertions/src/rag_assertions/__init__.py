"""Deterministic post-generation validation for grounded LLM/RAG outputs."""

from .assertions import (
    DateGroundedAssertion,
    EntityExistsAssertion,
    MetricsGroundedAssertion,
    NoFabricatedDatesAssertion,
    ProjectExistsAssertion,
    ScopeBoundedAssertion,
    TechnologyGroundedAssertion,
    TechStackGroundedAssertion,
)
from .base import AssertionProtocol, BaseAssertion
from .models import (
    AssertionResult,
    AssertionStatus,
    EvidenceItem,
    ValidationContext,
    ValidationResult,
)
from .runner import AssertionRunner

__version__ = "0.1.0"

__all__ = [
    "AssertionProtocol",
    "AssertionResult",
    "AssertionRunner",
    "AssertionStatus",
    "BaseAssertion",
    "DateGroundedAssertion",
    "EntityExistsAssertion",
    "EvidenceItem",
    "MetricsGroundedAssertion",
    "NoFabricatedDatesAssertion",
    "ProjectExistsAssertion",
    "ScopeBoundedAssertion",
    "TechStackGroundedAssertion",
    "TechnologyGroundedAssertion",
    "ValidationContext",
    "ValidationResult",
    "__version__",
]
