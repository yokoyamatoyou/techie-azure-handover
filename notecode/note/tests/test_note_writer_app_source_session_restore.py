from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _run_restore_probe(*, restore_enabled: bool) -> dict[str, object]:
    code = f"""
import json
from note import note_writer_app as app

app.RESTORE_PREVIOUS_SOURCES_ON_NEW_CLIENT = {restore_enabled!r}
app._CLIENT_STATES.clear()
app._COMMITTED_SOURCE_INVENTORY_SNAPSHOT.clear()
app._COMMITTED_SOURCE_SESSION_SNAPSHOT.clear()
app._snapshot_committed_source_inventory([
    app.SourceItem(
        id='source-1',
        label='Previous',
        value='https://example.com/previous',
        source_type='url',
    )
])
state = app._get_or_create_state('fresh-client')
print(json.dumps({{'sources': [source.value for source in state.sources]}}))
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout.strip())


def test_committed_source_inventory_is_not_restored_by_default() -> None:
    assert _run_restore_probe(restore_enabled=False) == {"sources": []}


def test_committed_source_inventory_restore_is_explicit_opt_in() -> None:
    assert _run_restore_probe(restore_enabled=True) == {
        "sources": ["https://example.com/previous"],
    }
