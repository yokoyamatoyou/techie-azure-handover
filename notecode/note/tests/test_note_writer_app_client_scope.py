from types import SimpleNamespace

from note.note_writer_app_client_scope import (
    CLIENT_SCOPE_DEFAULT,
    ClientScopeRegistry,
    client_key_from_client,
    is_detached_nicegui_error,
    normalize_client_key,
    run_attached_ui_mutation,
)


class _Timer:
    def __init__(self) -> None:
        self.deactivated = False

    def deactivate(self) -> None:
        self.deactivated = True


def test_client_key_helpers_keep_default_and_client_id_behavior() -> None:
    assert normalize_client_key(None) == CLIENT_SCOPE_DEFAULT
    assert normalize_client_key("abc") == "abc"
    assert client_key_from_client(None) == CLIENT_SCOPE_DEFAULT
    assert client_key_from_client(SimpleNamespace(id="client-1")) == "client-1"


def test_client_scope_registry_tracks_timer_and_generation_token() -> None:
    registry = ClientScopeRegistry()
    timer = _Timer()

    registry.activate("client-1")
    registry.register_timer("client-1", timer)
    token = registry.start_generation("client-1", "", token_factory=lambda: "generated-token")

    assert token == "generated-token"
    assert registry.generation_token_for("client-1") == "generated-token"
    assert registry.is_generation_attached("client-1", "generated-token") is True

    registry.finish_generation("client-1", "generated-token")
    assert registry.generation_token_for("client-1") == ""

    released_key = registry.release("client-1")
    assert released_key == "client-1"
    assert timer.deactivated is True
    assert registry.is_generation_attached("client-1", "generated-token") is False


def test_run_attached_mutation_handles_detached_runtime_error() -> None:
    registry = ClientScopeRegistry()
    detached: list[str] = []
    registry.activate("client-1")
    registry.start_generation("client-1", "token", token_factory=lambda: "unused")

    ran = registry.run_attached_mutation(
        client_key="client-1",
        generation_token="token",
        mutation=lambda: (_ for _ in ()).throw(RuntimeError("The parent slot of the element has been deleted.")),
        on_detached=detached.append,
    )

    assert ran is False
    assert detached == ["client-1"]
    assert is_detached_nicegui_error(RuntimeError("other")) is False


def test_run_attached_ui_mutation_logs_and_releases_detached_client() -> None:
    registry = ClientScopeRegistry()
    released: list[str] = []
    logs: list[tuple[tuple[object, ...], dict[str, object]]] = []
    registry.activate("client-1")
    registry.start_generation("client-1", "token", token_factory=lambda: "unused")

    ran = run_attached_ui_mutation(
        registry=registry,
        client_key="client-1",
        generation_token="token",
        mutation=lambda: (_ for _ in ()).throw(
            RuntimeError("The client this element belongs to has been deleted.")
        ),
        release_client_scope=released.append,
        log_info=lambda *args, **kwargs: logs.append((args, kwargs)),
        action_name="progress",
    )

    assert ran is False
    assert released == ["client-1"]
    assert logs and logs[0][0][1:] == ("client-1", "progress")
