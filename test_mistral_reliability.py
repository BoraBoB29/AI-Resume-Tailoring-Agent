import json

import httpx
import pytest

from src.llm_tailor import (
    ResumeTailor,
    _complete_with_retries,
    _is_retryable_mistral_error,
)
from src.jd_analyzer import extract_requirements


class FakeChat:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    def complete(self, **request):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class FakeClient:
    def __init__(self, outcomes):
        self.chat = FakeChat(outcomes)


def test_retries_read_timeout_then_returns_response(monkeypatch):
    monkeypatch.setenv("MISTRAL_MAX_RETRIES", "3")
    monkeypatch.setenv("MISTRAL_RETRY_BACKOFF_SECONDS", "1")
    client = FakeClient([httpx.ReadTimeout("temporary"), "success"])

    result = _complete_with_retries(client, {"model": "test-model"})

    assert result == "success"
    assert client.chat.calls == 2


def test_retries_rate_limit_and_server_errors(monkeypatch):
    monkeypatch.setenv("MISTRAL_MAX_RETRIES", "3")
    error_429 = RuntimeError("rate limited")
    error_429.status_code = 429
    error_500 = RuntimeError("server error")
    error_500.status_code = 503
    client = FakeClient([error_429, error_500, "success"])

    assert _complete_with_retries(client, {}) == "success"
    assert client.chat.calls == 3


def test_stops_after_configured_retry_limit(monkeypatch):
    monkeypatch.setenv("MISTRAL_MAX_RETRIES", "2")
    client = FakeClient([httpx.ReadTimeout("one"), httpx.ReadTimeout("two"), httpx.ReadTimeout("three")])

    with pytest.raises(httpx.ReadTimeout):
        _complete_with_retries(client, {})

    assert client.chat.calls == 3


def test_does_not_retry_non_transient_errors():
    client = FakeClient([ValueError("invalid request")])

    with pytest.raises(ValueError, match="invalid request"):
        _complete_with_retries(client, {})

    assert client.chat.calls == 1
    assert _is_retryable_mistral_error(ValueError("programming error")) is False


def test_constructor_uses_configurable_timeout(monkeypatch):
    captured = {}

    class FakeMistral:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setenv("MISTRAL_TIMEOUT_MS", "240000")
    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    monkeypatch.setattr("src.llm_tailor.Mistral", FakeMistral)

    ResumeTailor()

    assert captured["timeout_ms"] == 240000
    assert captured["api_key"] == "test-key"


def test_jd_analyzer_uses_timeout_and_retries_transient_failure(monkeypatch):
    captured = {}

    class FakeMistral:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.chat = FakeChat([
                httpx.ReadTimeout("temporary"),
                type(
                    "Response",
                    (),
                    {
                        "choices": [
                            type(
                                "Choice",
                                (),
                                {
                                    "message": type(
                                        "Message",
                                        (),
                                        {
                                            "content": json.dumps({
                                                "requirements": [{
                                                    "requirement": "SQL",
                                                    "evidence_level": "required",
                                                    "supporting_evidence": [],
                                                }]
                                            })
                                        },
                                    )()
                                },
                            )()
                        ]
                    },
                )(),
            ])

    monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
    monkeypatch.setenv("MISTRAL_TIMEOUT_MS", "240000")
    monkeypatch.setenv("MISTRAL_MAX_RETRIES", "3")
    monkeypatch.setattr("src.jd_analyzer.Mistral", FakeMistral)

    result = extract_requirements("A sufficiently long job description.")

    assert result[0].requirement == "SQL"
    assert captured["timeout_ms"] == 240000
