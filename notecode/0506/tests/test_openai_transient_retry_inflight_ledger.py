import json
from pathlib import Path

import pytest

from app.services.llm_client import OPENAI_UNSUPPORTED_SCHEMA_KEYS, OpenAIResponsesClient, _schema_for_openai_response_format
from app.services.schema_validator import load_schema, validate_payload


class FakeResponse:
    def __init__(self, output_text: str, response_id: str = "resp_fake") -> None:
        self.output_text = output_text
        self.id = response_id
        self._request_id = f"req_{response_id}"


class FakeStatusError(Exception):
    def __init__(self, status_code: int, message: str = "fake status error") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.request_id = f"req_error_{status_code}"


class FakeResponses:
    def __init__(self, outcomes: list[object]) -> None:
        self.outcomes = list(outcomes)
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs):  # type: ignore[no-untyped-def]
        self.calls.append(kwargs)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class FakeOpenAIClient:
    def __init__(self, outcomes: list[object]) -> None:
        self.responses = FakeResponses(outcomes)


def _source_card_json(source_id: str = "src_1") -> str:
    return json.dumps(
        {
            "source_id": source_id,
            "source_type": "manual",
            "title": "Source",
            "published_or_updated_at": None,
            "reliability": "user_uploaded",
            "main_topics": ["topic"],
            "facts": [
                {
                    "fact_id": "F001",
                    "claim": "We support consultations.",
                    "category": "service",
                    "importance": 4,
                    "source_span": "manual:1",
                    "usable_in_article": True,
                    "confidence": "high",
                    "risk_flags": [],
                }
            ],
            "quotes_or_phrases": [],
            "warnings": [],
            "metadata": {"source_label": "Source"},
        },
        ensure_ascii=False,
    )


def _payload(source_id: str = "src_1") -> dict:
    return {
        "source_packet": {
            "source_id": source_id,
            "source_type": "manual",
            "title": "Source",
            "chunks": [],
            "metadata": {},
            "warnings": [],
        }
    }


def _client(fake: FakeOpenAIClient, ledger: Path, max_retries: int = 2) -> OpenAIResponsesClient:
    client = OpenAIResponsesClient(
        client=fake,
        max_source_card_retries=max_retries,
        request_timeout_seconds=10,
        initial_backoff_seconds=0,
        max_backoff_seconds=0,
        jitter_seconds=0,
        sleep_func=lambda _seconds: None,
        random_func=lambda: 0,
    )
    client.set_inflight_ledger_path(ledger)
    return client


def _ledger_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _contains_key(value: object, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(_contains_key(item, key) for item in value.values())
    if isinstance(value, list):
        return any(_contains_key(item, key) for item in value)
    return False


def _find_keys(value: object, keys: set[str], path: str = "$") -> list[tuple[str, str]]:
    hits: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for item_key, item_value in value.items():
            if item_key in keys:
                hits.append((path, item_key))
            hits.extend(_find_keys(item_value, keys, f"{path}.{item_key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            hits.extend(_find_keys(item, keys, f"{path}[{index}]"))
    return hits


def _object_schema_gaps(value: object, path: str = "$") -> list[str]:
    gaps: list[str] = []
    if isinstance(value, dict):
        if value.get("type") == "object" and isinstance(value.get("properties"), dict):
            properties = set(value["properties"])
            required = set(value.get("required") or [])
            if properties != required:
                gaps.append(f"{path}: required mismatch")
            if value.get("additionalProperties") is not False:
                gaps.append(f"{path}: additionalProperties is not false")
        for item_key, item_value in value.items():
            gaps.extend(_object_schema_gaps(item_value, f"{path}.{item_key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            gaps.extend(_object_schema_gaps(item, f"{path}[{index}]"))
    return gaps


@pytest.mark.parametrize(
    "schema_name",
    [
        "source_card.schema.json",
        "knowledge_pack.schema.json",
        "article_brief.schema.json",
        "quality_check.schema.json",
        "publish_readiness.schema.json",
    ],
)
def test_openai_response_schema_sanitizer_removes_unsupported_keywords_and_strictifies_objects(schema_name: str) -> None:
    sent_schema = _schema_for_openai_response_format(load_schema(schema_name))

    assert _find_keys(sent_schema, OPENAI_UNSUPPORTED_SCHEMA_KEYS) == []
    assert _object_schema_gaps(sent_schema) == []


def test_openai_source_card_response_normalizes_trace_ids_before_local_validation(tmp_path: Path) -> None:
    response = json.loads(_source_card_json("Source URL 1"))
    response["main_topics"] = ["topic", "topic"]
    response["facts"][0]["fact_id"] = "fact_001"
    response["facts"][0]["importance"] = 10
    response["facts"][0]["risk_flags"] = ["unsupported", "unsupported"]
    response["metadata"]["source_priority"] = 0
    fake = FakeOpenAIClient([FakeResponse(json.dumps(response, ensure_ascii=False))])
    client = _client(fake, tmp_path / "openai_inflight_ledger.jsonl", max_retries=0)

    result = client.generate_json(
        "source_card_extraction",
        "Extract source-grounded facts only. Do not infer missing facts.",
        _payload("Source URL 1"),
        "source_card.schema.json",
    )

    assert result["source_id"] == "source_url_1"
    assert result["main_topics"] == ["topic"]
    assert result["facts"][0]["fact_id"] == "F001"
    assert result["facts"][0]["importance"] == 5
    assert result["facts"][0]["risk_flags"] == ["unsupported"]
    assert result["metadata"]["source_priority"] == 1
    validate_payload("source_card.schema.json", result)


def test_openai_knowledge_pack_response_normalizes_claim_and_fact_references() -> None:
    fake = FakeOpenAIClient(
        [
            FakeResponse(
                json.dumps(
                    {
                        "article_knowledge_pack": {
                            "pack_id": "pack_1",
                            "source_card_ids": ["source_url_1", "source_url_1"],
                            "confirmed_facts": [
                                {
                                    "claim_id": "claim_001",
                                    "claim": "We support consultations.",
                                    "supporting_fact_ids": ["fact_001", "fact_001"],
                                    "confidence": "high",
                                    "preferred_expression": "We support consultations.",
                                    "risk_flags": ["unsupported", "unsupported"],
                                }
                            ],
                            "conflicts": [
                                {
                                    "issue": "date mismatch",
                                    "involved_fact_ids": ["fact_001", "fact_002", "fact_002"],
                                    "resolution": "Do not mention the date.",
                                    "do_not_mention": True,
                                }
                            ],
                            "deduped_themes": ["consultation", "consultation"],
                            "do_not_infer": ["unsupported superiority"],
                        }
                    }
                )
            )
        ]
    )
    client = OpenAIResponsesClient(
        client=fake,
        request_timeout_seconds=10,
        initial_backoff_seconds=0,
        max_backoff_seconds=0,
        jitter_seconds=0,
        sleep_func=lambda _seconds: None,
        random_func=lambda: 0,
    )

    result = client.generate_json(
        "knowledge_pack_integration",
        "Merge source cards into confirmed claims and conflicts.",
        {"source_cards": []},
        "knowledge_pack.schema.json",
    )

    pack = result["article_knowledge_pack"]
    assert pack["source_card_ids"] == ["source_url_1"]
    assert pack["confirmed_facts"][0]["claim_id"] == "C001"
    assert pack["confirmed_facts"][0]["supporting_fact_ids"] == ["F001"]
    assert pack["confirmed_facts"][0]["risk_flags"] == ["unsupported"]
    assert pack["conflicts"][0]["involved_fact_ids"] == ["F001", "F002"]
    assert pack["deduped_themes"] == ["consultation"]
    validate_payload("knowledge_pack.schema.json", result)


def test_openai_knowledge_pack_response_drops_single_fact_conflicts() -> None:
    fake = FakeOpenAIClient(
        [
            FakeResponse(
                json.dumps(
                    {
                        "article_knowledge_pack": {
                            "pack_id": "pack_1",
                            "source_card_ids": ["source_url_1"],
                            "confirmed_facts": [
                                {
                                    "claim_id": "claim_001",
                                    "claim": "Exploration reports need setup.",
                                    "supporting_fact_ids": ["fact_002"],
                                    "confidence": "high",
                                    "preferred_expression": "Exploration reports need setup.",
                                    "risk_flags": [],
                                }
                            ],
                            "conflicts": [
                                {
                                    "issue": "single fact caveat",
                                    "involved_fact_ids": ["fact_002"],
                                    "resolution": "Do not treat it as a source conflict.",
                                    "do_not_mention": True,
                                }
                            ],
                            "deduped_themes": ["GA4"],
                            "do_not_infer": [],
                        }
                    }
                )
            )
        ]
    )
    client = OpenAIResponsesClient(
        client=fake,
        request_timeout_seconds=10,
        initial_backoff_seconds=0,
        max_backoff_seconds=0,
        jitter_seconds=0,
        sleep_func=lambda _seconds: None,
        random_func=lambda: 0,
    )

    result = client.generate_json(
        "knowledge_pack_integration",
        "Merge source cards into confirmed claims and conflicts.",
        {"source_cards": []},
        "knowledge_pack.schema.json",
    )

    assert result["article_knowledge_pack"]["conflicts"] == []
    validate_payload("knowledge_pack.schema.json", result)


def test_openai_gpt41_request_uses_temperature_without_reasoning(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4.1")
    monkeypatch.setenv("ROUTE_0506_OPENAI_TEMPERATURE", "0.9")
    fake = FakeOpenAIClient([FakeResponse(_source_card_json())])
    client = OpenAIResponsesClient(
        client=fake,
        request_timeout_seconds=10,
        initial_backoff_seconds=0,
        max_backoff_seconds=0,
        jitter_seconds=0,
        sleep_func=lambda _seconds: None,
        random_func=lambda: 0,
    )

    client.generate_json(
        "source_card_extraction",
        "Extract source-grounded facts only. Do not infer missing facts.",
        _payload(),
        "source_card.schema.json",
    )

    assert fake.responses.calls[0]["model"] == "gpt-4.1"
    assert fake.responses.calls[0]["temperature"] == 0.9
    assert "reasoning" not in fake.responses.calls[0]
    assert client.retry_controller.reasoning_effort == ""


def test_source_card_transient_error_retries_same_payload_and_records_success(tmp_path: Path) -> None:
    fake = FakeOpenAIClient([FakeStatusError(502), FakeResponse(_source_card_json(), "resp_success")])
    ledger = tmp_path / "openai_inflight_ledger.jsonl"
    client = _client(fake, ledger)
    payload = _payload()

    result = client.generate_json(
        "source_card_extraction",
        "Extract source-grounded facts only. Do not infer missing facts.",
        payload,
        "source_card.schema.json",
    )

    assert result["source_id"] == "src_1"
    assert len(fake.responses.calls) == 2
    first_user_input = fake.responses.calls[0]["input"][1]["content"]
    second_user_input = fake.responses.calls[1]["input"][1]["content"]
    assert first_user_input == second_user_input
    assert fake.responses.calls[0]["input"][0] == fake.responses.calls[1]["input"][0]
    assert fake.responses.calls[0]["model"] == fake.responses.calls[1]["model"] == "gpt-5.4-mini"
    assert fake.responses.calls[0]["reasoning"] == fake.responses.calls[1]["reasoning"] == {"effort": "high"}
    assert fake.responses.calls[0]["timeout"] == fake.responses.calls[1]["timeout"] == 10
    sent_schema = fake.responses.calls[0]["text"]["format"]["schema"]
    assert not _contains_key(sent_schema, "uniqueItems")
    assert "risk_flags" in sent_schema["$defs"]["fact"]["required"]
    rows = _ledger_rows(ledger)
    assert [row["status"] for row in rows] == ["inflight_unmetered", "failed", "inflight_unmetered", "success"]
    assert rows[-1]["response_id"] == "resp_success"
    assert rows[-1]["packet_id"] == "src_1"
    assert rows[-1]["actual_usage_available"] is False


def test_source_card_non_transient_error_is_not_retried(tmp_path: Path) -> None:
    fake = FakeOpenAIClient([FakeStatusError(400)])
    ledger = tmp_path / "openai_inflight_ledger.jsonl"
    client = _client(fake, ledger)

    with pytest.raises(FakeStatusError):
        client.generate_json("source_card_extraction", "instructions", _payload(), "source_card.schema.json")

    assert len(fake.responses.calls) == 1
    rows = _ledger_rows(ledger)
    assert [row["status"] for row in rows] == ["inflight_unmetered", "failed"]
    assert rows[-1]["error_status_code"] == 400
    assert rows[-1]["will_retry"] is False


def test_non_source_json_stage_retries_retryable_520_and_records_success(tmp_path: Path) -> None:
    fake = FakeOpenAIClient([FakeStatusError(520), FakeResponse('{"ok": true}', "resp_json_success")])
    ledger = tmp_path / "openai_inflight_ledger.jsonl"
    client = _client(fake, ledger)

    result = client.generate_json(
        "article_brief_builder",
        "Build an article brief.",
        {"knowledge_pack": {}},
        "article_brief.schema.json",
    )

    assert result == {"ok": True}
    assert len(fake.responses.calls) == 2
    rows = _ledger_rows(ledger)
    assert [row["status"] for row in rows] == ["inflight_unmetered", "failed", "inflight_unmetered", "success"]
    assert rows[1]["stage"] == "article_brief_builder"
    assert rows[1]["error_status_code"] == 520
    assert rows[1]["will_retry"] is True
    assert rows[-1]["response_id"] == "resp_json_success"


def test_source_card_retry_exhaustion_records_failed(tmp_path: Path) -> None:
    fake = FakeOpenAIClient([FakeStatusError(503), FakeStatusError(503), FakeStatusError(503)])
    ledger = tmp_path / "openai_inflight_ledger.jsonl"
    client = _client(fake, ledger, max_retries=2)

    with pytest.raises(FakeStatusError):
        client.generate_json("source_card_extraction", "instructions", _payload(), "source_card.schema.json")

    assert len(fake.responses.calls) == 3
    rows = _ledger_rows(ledger)
    assert [row["status"] for row in rows] == [
        "inflight_unmetered",
        "failed",
        "inflight_unmetered",
        "failed",
        "inflight_unmetered",
        "failed",
    ]
    assert rows[-1]["will_retry"] is False


def test_source_card_timeout_records_timeout_terminal_status(tmp_path: Path) -> None:
    fake = FakeOpenAIClient([TimeoutError("timed out")])
    ledger = tmp_path / "openai_inflight_ledger.jsonl"
    client = _client(fake, ledger, max_retries=0)

    with pytest.raises(TimeoutError):
        client.generate_json("source_card_extraction", "instructions", _payload(), "source_card.schema.json")

    rows = _ledger_rows(ledger)
    assert [row["status"] for row in rows] == ["inflight_unmetered", "timeout"]
    assert rows[-1]["error_type"] == "TimeoutError"


def test_draft_writer_transient_error_retries_once_and_records_success(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ROUTE_0506_DRAFT_WRITER_MAX_RETRIES", "1")
    fake = FakeOpenAIClient([FakeStatusError(502), FakeResponse("draft text", "resp_draft")])
    ledger = tmp_path / "openai_inflight_ledger.jsonl"
    client = _client(fake, ledger)
    payload = {"article_brief": {"article_brief": {"category": "company_service_intro"}}, "knowledge_pack": {}}

    result = client.generate_text("draft_writer", "Write the first draft.", payload)

    assert result == "draft text"
    assert len(fake.responses.calls) == 2
    assert fake.responses.calls[0]["input"] == fake.responses.calls[1]["input"]
    assert fake.responses.calls[0]["model"] == fake.responses.calls[1]["model"] == "gpt-5.4-mini"
    assert fake.responses.calls[0]["reasoning"] == fake.responses.calls[1]["reasoning"] == {"effort": "high"}
    rows = _ledger_rows(ledger)
    assert [row["status"] for row in rows] == ["inflight_unmetered", "failed", "inflight_unmetered", "success"]
    assert {row["stage"] for row in rows} == {"draft_writer"}
    assert rows[1]["will_retry"] is True
    assert rows[-1]["max_retries"] == 1
    assert rows[-1]["usage_status"] == "requested_unmetered"
    assert rows[-1]["actual_usage_available"] is False


def test_draft_writer_retry_exhaustion_records_timeout_and_reraises(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ROUTE_0506_DRAFT_WRITER_MAX_RETRIES", "1")
    fake = FakeOpenAIClient([TimeoutError("timed out"), TimeoutError("timed out again")])
    ledger = tmp_path / "openai_inflight_ledger.jsonl"
    client = _client(fake, ledger)

    with pytest.raises(TimeoutError):
        client.generate_text("draft_writer", "instructions", {"article_brief": {}, "knowledge_pack": {}})

    assert len(fake.responses.calls) == 2
    rows = _ledger_rows(ledger)
    assert [row["status"] for row in rows] == ["inflight_unmetered", "timeout", "inflight_unmetered", "timeout"]
    assert rows[1]["will_retry"] is True
    assert rows[-1]["will_retry"] is False


def test_draft_writer_permanent_403_is_not_retried(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ROUTE_0506_DRAFT_WRITER_MAX_RETRIES", "1")
    fake = FakeOpenAIClient([FakeStatusError(403)])
    ledger = tmp_path / "openai_inflight_ledger.jsonl"
    client = _client(fake, ledger)

    with pytest.raises(FakeStatusError):
        client.generate_text("draft_writer", "instructions", {"article_brief": {}, "knowledge_pack": {}})

    assert len(fake.responses.calls) == 1
    rows = _ledger_rows(ledger)
    assert [row["status"] for row in rows] == ["inflight_unmetered", "failed"]
    assert rows[-1]["error_status_code"] == 403
    assert rows[-1]["will_retry"] is False


@pytest.mark.parametrize(
    "stage_name",
    ["opening_editor", "global_consistency_editor", "style_editor", "structural_editor"],
)
def test_editor_text_stage_retries_transient_error_and_records_ledger(
    stage_name: str,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("ROUTE_0506_EDITOR_STAGE_MAX_RETRIES", "1")
    fake = FakeOpenAIClient([FakeStatusError(503), FakeResponse("edited text", "resp_editor")])
    ledger = tmp_path / "openai_inflight_ledger.jsonl"
    client = _client(fake, ledger)

    result = client.generate_text(stage_name, "instructions", {"draft": "text"})

    assert result == "edited text"
    assert len(fake.responses.calls) == 2
    rows = _ledger_rows(ledger)
    assert [row["status"] for row in rows] == ["inflight_unmetered", "failed", "inflight_unmetered", "success"]
    assert {row["stage"] for row in rows} == {stage_name}
    assert rows[1]["will_retry"] is True
    assert rows[-1]["max_retries"] == 1


def test_structural_editor_520_honors_server_retry_after_hint(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ROUTE_0506_EDITOR_STAGE_MAX_RETRIES", "1")
    monkeypatch.setenv("ROUTE_0506_OPENAI_RETRY_MAX_SERVER_HINT_SECONDS", "120")
    waits: list[float] = []
    fake = FakeOpenAIClient(
        [
            FakeStatusError(520, "Error code: 520 - {'retry_after': 60}"),
            FakeResponse("edited text", "resp_structural"),
        ]
    )
    ledger = tmp_path / "openai_inflight_ledger.jsonl"
    client = OpenAIResponsesClient(
        client=fake,
        request_timeout_seconds=10,
        initial_backoff_seconds=10,
        max_backoff_seconds=10,
        jitter_seconds=0,
        sleep_func=waits.append,
        random_func=lambda: 0,
    )
    client.set_inflight_ledger_path(ledger)

    result = client.generate_text("structural_editor", "instructions", {"draft": "text"})

    assert result == "edited text"
    assert waits == [60.0]
    rows = _ledger_rows(ledger)
    assert rows[1]["error_status_code"] == 520
    assert rows[1]["retry_after_seconds"] == 60.0
    assert rows[1]["will_retry"] is True
    assert rows[-1]["stage"] == "structural_editor"


def test_non_source_json_stage_retry_exhaustion_records_failed(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ROUTE_0506_JSON_STAGE_MAX_RETRIES", "1")
    fake = FakeOpenAIClient([FakeStatusError(503), FakeStatusError(503)])
    ledger = tmp_path / "openai_inflight_ledger.jsonl"
    client = _client(fake, ledger)

    with pytest.raises(FakeStatusError):
        client.generate_json("knowledge_pack_integration", "instructions", {"source_cards": []}, "knowledge_pack.schema.json")

    assert len(fake.responses.calls) == 2
    rows = _ledger_rows(ledger)
    assert [row["status"] for row in rows] == ["inflight_unmetered", "failed", "inflight_unmetered", "failed"]
    assert rows[1]["will_retry"] is True
    assert rows[-1]["will_retry"] is False
