import os

import uvicorn
from fastapi import FastAPI
from nicegui import ui

from note import note_writer_app  # noqa: F401


app = FastAPI()
ui.run_with(
    app,
    title="コトメイク | TECHIE",
    favicon=str(note_writer_app.STATIC_DIR / "favicon_v2.png"),
    show_welcome_message=False,
)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "8080")), reload=False)
