"""Primitive ReAct-style loop built on Anthropic's native tool_use API."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rag_assertions import AssertionRunner, EvidenceItem, ValidationResult
from rag.vector_store import VectorStore

from .tools import ANTHROPIC_TOOLS, AgentTools
from .traces import DEFAULT_TRACE_DIR, TraceLogger

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_ITERATIONS = 5
DEFAULT_MAX_TOKENS = 1200

SYSTEM_PROMPT = """\
You answer questions about Ahmad's indexed portfolio projects.

Use the available tools to inspect the corpus before answering. Think briefly
in text, call tools when you need evidence, and answer only from tool results.
If the project documentation does not contain enough information, say so.
End final answers with a concise Sources line naming the citations you used.
"""


@dataclass
class AgentResult:
    question: str
    answer: str
    messages: list[dict[str, Any]]
    trace_path: str
    session_id: str
    iterations: int
    validation: ValidationResult | None = None
    retry_triggered: bool = False
    token_usage: dict[str, int] | None = None


class ReActAgent:
    def __init__(
        self,
        store: VectorStore,
        client: Any | None = None,
        model: str | None = None,
        trace_dir: Path = DEFAULT_TRACE_DIR,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        assertion_runner: AssertionRunner | None = None,
        enable_assertions: bool = True,
    ) -> None:
        self.store = store
        self.client = client or self._default_client()
        self.model = model or os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
        self.max_tokens = max_tokens
        self.trace_dir = trace_dir
        self.assertion_runner = assertion_runner or AssertionRunner()
        self.enable_assertions = enable_assertions

    def ask(
        self, question: str, max_iterations: int = DEFAULT_MAX_ITERATIONS
    ) -> AgentResult:
        tracer = TraceLogger(self.trace_dir)
        tools = AgentTools(self.store)
        messages: list[dict[str, Any]] = [{"role": "user", "content": question}]
        evidence: list[EvidenceItem] = []
        project_registry = tools.list_projects()["projects"]

        tracer.log("session_start", question=question, max_iterations=max_iterations)
        final_answer = ""
        iterations = 0
        token_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

        for iteration in range(1, max_iterations + 1):
            iterations = iteration
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=0,
                system=SYSTEM_PROMPT,
                messages=messages,
                tools=ANTHROPIC_TOOLS,
            )
            _add_usage(token_usage, response)
            assistant_content = [_serialize_block(block) for block in response.content]
            messages.append({"role": "assistant", "content": assistant_content})

            text_blocks = [
                block.get("text", "")
                for block in assistant_content
                if block.get("type") == "text"
            ]
            thought_text = "\n".join(t for t in text_blocks if t).strip()
            tool_uses = [
                block for block in assistant_content if block.get("type") == "tool_use"
            ]
            tracer.log(
                "iteration",
                iteration=iteration,
                thought=thought_text,
                tool_calls=[
                    {
                        "id": call.get("id"),
                        "name": call.get("name"),
                        "input": call.get("input", {}),
                    }
                    for call in tool_uses
                ],
            )

            if not tool_uses:
                final_answer = thought_text
                tracer.log("draft_answer", answer=final_answer, iterations=iteration)
                if not self.enable_assertions:
                    tracer.log(
                        "validation_skipped",
                        reason="Assertions disabled for this agent run.",
                    )
                    tracer.log("final_answer", answer=final_answer, iterations=iteration)
                    return AgentResult(
                        question=question,
                        answer=final_answer,
                        messages=messages,
                        trace_path=str(tracer.path),
                        session_id=tracer.session_id,
                        iterations=iterations,
                        validation=None,
                        retry_triggered=False,
                        token_usage=token_usage,
                    )
                return self._validate_and_finalize(
                    question=question,
                    draft_answer=final_answer,
                    messages=messages,
                    evidence=evidence,
                    project_registry=project_registry,
                    tracer=tracer,
                    iterations=iterations,
                    token_usage=token_usage,
                )

            tool_results = []
            for call in tool_uses:
                result = tools.execute(call.get("name", ""), call.get("input", {}))
                evidence.extend(
                    _evidence_from_tool_result(call.get("name", ""), call.get("input", {}), result)
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": call.get("id"),
                        "content": _stringify_tool_result(result),
                    }
                )
                tracer.log(
                    "tool_result",
                    iteration=iteration,
                    tool_use_id=call.get("id"),
                    tool_name=call.get("name"),
                    result=result,
                )
            messages.append({"role": "user", "content": tool_results})

        final_answer = (
            "Stopped after reaching max_iterations before Claude returned a final "
            "text-only answer."
        )
        tracer.log("max_iterations_reached", answer=final_answer, iterations=iterations)
        return AgentResult(
            question=question,
            answer=final_answer,
            messages=messages,
            trace_path=str(tracer.path),
            session_id=tracer.session_id,
            iterations=iterations,
            token_usage=token_usage,
        )

    def _validate_and_finalize(
        self,
        question: str,
        draft_answer: str,
        messages: list[dict[str, Any]],
        evidence: list[EvidenceItem],
        project_registry: list[str],
        tracer: TraceLogger,
        iterations: int,
        token_usage: dict[str, int],
    ) -> AgentResult:
        validation = self.assertion_runner.validate(
            answer=draft_answer,
            retrieved_context=evidence,
            project_registry=project_registry,
            question=question,
        )
        tracer.log(
            "validation",
            stage="draft",
            validation=validation.to_dict(),
            evidence=[item.to_dict() for item in evidence],
        )
        if validation.all_passed:
            tracer.log("final_answer", answer=draft_answer, iterations=iterations)
            return AgentResult(
                question=question,
                answer=draft_answer,
                messages=messages,
                trace_path=str(tracer.path),
                session_id=tracer.session_id,
                iterations=iterations,
                validation=validation,
                retry_triggered=False,
                token_usage=token_usage,
            )

        correction_prompt = _build_correction_prompt(validation)
        tracer.log(
            "correction_retry",
            retry_number=1,
            failed_assertions=[result.to_dict() for result in validation.failed],
        )
        messages.append({"role": "user", "content": correction_prompt})
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=0,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        _add_usage(token_usage, response)
        corrected_content = [_serialize_block(block) for block in response.content]
        messages.append({"role": "assistant", "content": corrected_content})
        corrected_answer = _text_from_content(corrected_content)
        tracer.log("corrected_answer", answer=corrected_answer)

        second_validation = self.assertion_runner.validate(
            answer=corrected_answer,
            retrieved_context=evidence,
            project_registry=project_registry,
            question=question,
        )
        tracer.log(
            "validation",
            stage="corrected",
            validation=second_validation.to_dict(),
            evidence=[item.to_dict() for item in evidence],
        )
        if second_validation.all_passed:
            tracer.log("final_answer", answer=corrected_answer, iterations=iterations)
            return AgentResult(
                question=question,
                answer=corrected_answer,
                messages=messages,
                trace_path=str(tracer.path),
                session_id=tracer.session_id,
                iterations=iterations,
                validation=second_validation,
                retry_triggered=True,
                token_usage=token_usage,
            )

        safe_answer = _safe_unverifiable_answer(second_validation)
        tracer.log(
            "validation_failed_final",
            answer=safe_answer,
            failed_assertions=[result.to_dict() for result in second_validation.failed],
        )
        tracer.log("final_answer", answer=safe_answer, iterations=iterations)
        return AgentResult(
            question=question,
            answer=safe_answer,
            messages=messages,
            trace_path=str(tracer.path),
            session_id=tracer.session_id,
            iterations=iterations,
            validation=second_validation,
            retry_triggered=True,
            token_usage=token_usage,
        )

    @staticmethod
    def _default_client():
        from anthropic import Anthropic

        return Anthropic()


def _serialize_block(block: Any) -> dict[str, Any]:
    if isinstance(block, dict):
        return block
    if hasattr(block, "model_dump"):
        return block.model_dump(exclude_none=True)
    data = {"type": getattr(block, "type", "")}
    for attr in ("text", "id", "name", "input"):
        if hasattr(block, attr):
            data[attr] = getattr(block, attr)
    return data


def _add_usage(total: dict[str, int], response: Any) -> None:
    usage = getattr(response, "usage", None)
    if usage is None:
        return
    input_tokens = _usage_value(usage, "input_tokens")
    output_tokens = _usage_value(usage, "output_tokens")
    total["input_tokens"] += input_tokens
    total["output_tokens"] += output_tokens
    total["total_tokens"] += input_tokens + output_tokens


def _usage_value(usage: Any, name: str) -> int:
    if isinstance(usage, dict):
        return int(usage.get(name) or 0)
    return int(getattr(usage, name, 0) or 0)


def _stringify_tool_result(result: dict[str, Any]) -> str:
    import json

    return json.dumps(result, ensure_ascii=False)


def _text_from_content(content: list[dict[str, Any]]) -> str:
    return "\n".join(
        block.get("text", "") for block in content if block.get("type") == "text"
    ).strip()


def _evidence_from_tool_result(
    tool_name: str, tool_input: dict[str, Any] | None, result: dict[str, Any]
) -> list[EvidenceItem]:
    tool_input = tool_input or {}
    if tool_name == "search_technical_details":
        return [
            EvidenceItem(
                text=item.get("text", ""),
                source=item.get("citation", ""),
                entity=result.get("project_name"),
                score=item.get("score"),
                metadata={
                    "tool_name": tool_name,
                    "query": result.get("query") or tool_input.get("query"),
                },
            )
            for item in result.get("results", [])
        ]
    if tool_name == "get_project_summary" and result.get("summary"):
        return [
            EvidenceItem(
                text=result.get("summary", ""),
                source=f"{result.get('project_name')} > summary",
                entity=result.get("project_name"),
                metadata={"tool_name": tool_name},
            )
        ]
    return []


def _build_correction_prompt(validation: ValidationResult) -> str:
    lines = [
        "Your previous answer failed factual grounding validation.",
        "",
        "Only answer using facts supported by the supplied evidence.",
        "Remove or correct unsupported claims.",
        "",
    ]
    for result in validation.failed:
        lines.extend(
            [
                f"Failed assertion: {result.assertion}",
                f"Unsupported claim: {result.claim}",
                f"Reason: {result.reason}",
                "",
            ]
        )
    return "\n".join(lines).strip()


def _safe_unverifiable_answer(validation: ValidationResult) -> str:
    failed = ", ".join(result.assertion for result in validation.failed)
    return (
        "I could not verify enough of the generated answer against the retrieved "
        f"project evidence, so I won't return it as factual. Failed assertions: {failed}."
    )
