from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from config import AppConfig

@dataclass
class SourceItem:
    url: str
    title: str
    kind: str


@dataclass
class AnalysisResult:
    keyword_raw: str
    keyword_norm: str
    output_text: str
    output_json: dict[str, Any]
    usage: dict[str, Any]
    web_search_calls: int
    sources: list[SourceItem]
    estimated_cost_usd: float = 0.0


@dataclass
class BatchRequestItem:
    custom_id: str
    keyword_raw: str
    keyword_norm: str
    iteration_index: int
    request_line: dict[str, Any]


@dataclass
class BatchJobHandle:
    batch_job_id: str
    status: str
    input_file_id: str
    endpoint: str
    completion_window: str
    output_file_id: str = ""
    error_file_id: str = ""
    request_counts_total: int = 0
    request_counts_completed: int = 0
    request_counts_failed: int = 0
    raw_batch: dict[str, Any] | None = None


@dataclass
class BatchImportRecord:
    custom_id: str
    remote_request_id: str
    response_status_code: int | None
    result: AnalysisResult | None
    error_text: str = ""


class ProviderClient(Protocol):
    def analyze_keyword(self, keyword: str, config: AppConfig) -> AnalysisResult:
        ...

    def submit_batch(
        self,
        config: AppConfig,
        execution_requests: list[dict[str, Any]] | None = None,
    ) -> tuple[BatchJobHandle, list[BatchRequestItem]]:
        ...

    def retrieve_batch(self, batch_job_id: str) -> BatchJobHandle:
        ...

    def import_batch_results(
        self,
        batch: BatchJobHandle,
        config: AppConfig,
        request_items: dict[str, dict[str, Any]],
    ) -> list[BatchImportRecord]:
        ...


class NotImplementedProviderClient:
    def __init__(self, provider_key: str) -> None:
        self.provider_key = provider_key

    def analyze_keyword(self, keyword: str, config: AppConfig) -> AnalysisResult:
        raise NotImplementedError(
            f"provider '{self.provider_key}' is not wired yet. "
            "Check the provider registry for currently live adapters."
        )

    def submit_batch(
        self,
        config: AppConfig,
        execution_requests: list[dict[str, Any]] | None = None,
    ) -> tuple[BatchJobHandle, list[BatchRequestItem]]:
        raise NotImplementedError(
            f"provider '{self.provider_key}' does not support Batch mode in this PoC."
        )

    def retrieve_batch(self, batch_job_id: str) -> BatchJobHandle:
        raise NotImplementedError(
            f"provider '{self.provider_key}' does not support Batch mode in this PoC."
        )

    def import_batch_results(
        self,
        batch: BatchJobHandle,
        config: AppConfig,
        request_items: dict[str, dict[str, Any]],
    ) -> list[BatchImportRecord]:
        raise NotImplementedError(
            f"provider '{self.provider_key}' does not support Batch mode in this PoC."
        )


