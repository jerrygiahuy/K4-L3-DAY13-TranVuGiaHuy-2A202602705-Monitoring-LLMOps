from __future__ import annotations

from contextlib import contextmanager

from app import agent as agent_module
from app import mock_llm, mock_rag


class ManagedPrompt:
    version = 3

    def compile(self, **variables: str) -> str:
        return (
            f"Feature={variables['feature']}\n"
            f"Docs={variables['docs']}\n"
            f"Question={variables['message']}"
        )


class RecordingLangfuseClient:
    def __init__(self) -> None:
        self.prompt = ManagedPrompt()
        self.span_updates: list[dict] = []

    def get_prompt(self, name: str, **kwargs):
        return self.prompt

    def update_current_span(self, **kwargs) -> None:
        self.span_updates.append(kwargs)


def test_agent_records_prompt_version_with_v4_observation_api(monkeypatch) -> None:
    monkeypatch.setenv("LANGFUSE_PROMPT_NAME", "day13-chat")
    monkeypatch.setenv("LANGFUSE_PROMPT_LABEL", "production")
    client = RecordingLangfuseClient()
    monkeypatch.setattr(agent_module, "get_langfuse_client", lambda: client)
    monkeypatch.setattr(agent_module, "tracing_enabled", lambda: True)

    propagated: list[dict] = []

    @contextmanager
    def record_attributes(**kwargs):
        propagated.append(kwargs)
        yield

    monkeypatch.setattr(agent_module, "propagate_attributes", record_attributes)

    agent = agent_module.LabAgent()
    agent_module.LabAgent.run.__wrapped__(
        agent,
        user_id="student-01",
        feature="qa",
        session_id="session-01",
        message="Explain traces",
        correlation_id="req-12345678",
    )

    span_update = client.span_updates[-1]
    assert span_update["metadata"] == {
        "doc_count": 1,
        "query_preview": "Explain traces",
        "prompt_name": "day13-chat",
        "prompt_label": "production",
        "prompt_version": "3",
        "prompt_source": "langfuse",
        "prompt_fetch_error": "",
    }
    assert span_update["version"] == "3"
    assert propagated[0]["metadata"]["correlation_id"] == "req-12345678"
    assert propagated[-1]["prompt"] is client.prompt


class RecordingObservationClient:
    def __init__(self) -> None:
        self.span_updates: list[dict] = []
        self.generation_updates: list[dict] = []

    def update_current_span(self, **kwargs) -> None:
        self.span_updates.append(kwargs)

    def update_current_generation(self, **kwargs) -> None:
        self.generation_updates.append(kwargs)


def test_retrieval_child_observation_uses_safe_metadata(monkeypatch) -> None:
    client = RecordingObservationClient()
    monkeypatch.setattr(mock_rag, "get_langfuse_client", lambda: client)

    docs = mock_rag.retrieve.__wrapped__("Email student@vinuni.edu.vn asks about refund")

    assert docs
    metadata = client.span_updates[-1]["metadata"]
    assert metadata["doc_count"] == 1
    assert "student@" not in metadata["query_preview"]
    assert "REDACTED_EMAIL" in metadata["query_preview"]


def test_generation_child_observation_records_model_usage_cost_and_prompt(monkeypatch) -> None:
    client = RecordingObservationClient()
    monkeypatch.setattr(mock_llm, "get_langfuse_client", lambda: client)
    managed_prompt = object()

    response = mock_llm.FakeLLM().generate.__wrapped__(
        mock_llm.FakeLLM(),
        "Question from student@vinuni.edu.vn",
        managed_prompt=managed_prompt,
    )

    update = client.generation_updates[-1]
    assert update["model"] == response.model
    assert update["usage_details"]["input"] == response.usage.input_tokens
    assert update["usage_details"]["output"] == response.usage.output_tokens
    assert update["cost_details"]["total"] > 0
    assert update["prompt"] is managed_prompt
    assert "student@" not in update["metadata"]["prompt_preview"]
