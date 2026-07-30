"""Client-scope timer and generation-token registry for note_writer_app."""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Set


CLIENT_SCOPE_DEFAULT = "__global__"
DETACHED_NICEGUI_ERROR_TEXTS = (
    "The client this element belongs to has been deleted.",
    "The parent slot of the element has been deleted.",
    "The parent element this slot belongs to has been deleted.",
)


def normalize_client_key(client_key: Optional[str]) -> str:
    return str(client_key or CLIENT_SCOPE_DEFAULT)


def client_key_from_client(client: Any) -> str:
    if client and getattr(client, "id", None):
        return str(client.id)
    return CLIENT_SCOPE_DEFAULT


def is_detached_nicegui_error(exc: BaseException) -> bool:
    message = str(exc)
    return any(fragment in message for fragment in DETACHED_NICEGUI_ERROR_TEXTS)


def run_attached_ui_mutation(
    *,
    registry: "ClientScopeRegistry",
    client_key: str,
    generation_token: str,
    mutation: Callable[[], None],
    release_client_scope: Callable[[str], None],
    log_info: Callable[..., None],
    action_name: str = "ui_mutation",
) -> bool:
    def _on_detached(normalized_client_key: str) -> None:
        log_info(
            "Skipped stale UI mutation after client detach client_key=%s action=%s",
            normalized_client_key,
            action_name,
        )
        release_client_scope(normalized_client_key)

    return registry.run_attached_mutation(
        client_key=client_key,
        generation_token=generation_token,
        mutation=mutation,
        on_detached=_on_detached,
    )


class ClientScopeRegistry:
    def __init__(self) -> None:
        self.timers: Dict[str, List[Any]] = {}
        self.active_keys: Set[str] = set()
        self.generation_tokens: Dict[str, str] = {}

    def deactivate_timers(self, client_key: str) -> None:
        key = normalize_client_key(client_key)
        timers = self.timers.pop(key, [])
        for timer_obj in timers:
            try:
                timer_obj.deactivate()
            except Exception:
                continue

    def register_timer(self, client_key: str, timer_obj: Any) -> Any:
        key = normalize_client_key(client_key)
        self.timers.setdefault(key, []).append(timer_obj)
        return timer_obj

    def activate(self, client_key: str) -> None:
        key = normalize_client_key(client_key)
        self.active_keys.add(key)
        self.generation_tokens.pop(key, None)

    def release(self, client_key: str) -> str:
        key = normalize_client_key(client_key)
        self.deactivate_timers(key)
        self.active_keys.discard(key)
        self.generation_tokens.pop(key, None)
        return key

    def start_generation(
        self,
        client_key: str,
        generation_token: str,
        *,
        token_factory: Callable[[], str],
    ) -> str:
        key = normalize_client_key(client_key)
        token = str(generation_token or token_factory())
        if key in self.active_keys:
            self.generation_tokens[key] = token
        return token

    def finish_generation(self, client_key: str, generation_token: str) -> None:
        key = normalize_client_key(client_key)
        if generation_token and self.generation_tokens.get(key) == generation_token:
            self.generation_tokens.pop(key, None)

    def is_generation_attached(self, client_key: str, generation_token: str) -> bool:
        key = normalize_client_key(client_key)
        return bool(generation_token) and key in self.active_keys and self.generation_tokens.get(key) == generation_token

    def generation_token_for(self, client_key: str) -> str:
        return self.generation_tokens.get(normalize_client_key(client_key), "")

    def run_attached_mutation(
        self,
        *,
        client_key: str,
        generation_token: str,
        mutation: Callable[[], None],
        on_detached: Callable[[str], None],
    ) -> bool:
        if not self.is_generation_attached(client_key, generation_token):
            return False
        try:
            mutation()
            return True
        except RuntimeError as exc:
            if is_detached_nicegui_error(exc):
                on_detached(normalize_client_key(client_key))
                return False
            raise
