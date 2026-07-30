from note.article_helper_facade import ArticleHelperFacade


class _StubLLM:
    def generate_text(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return "[]"


def test_article_helper_facade_exposes_llm_and_status_helpers() -> None:
    llm = _StubLLM()
    helper = ArticleHelperFacade(llm_client=llm)  # type: ignore[arg-type]

    assert helper.llm is llm
    assert helper.get_last_interview_generation_status() == {
        "mode": "not_run",
        "reason": "",
    }


def test_article_helper_facade_progress_helpers_round_trip() -> None:
    helper = ArticleHelperFacade(llm_client=_StubLLM())  # type: ignore[arg-type]
    helper.reset_generation_progress()

    progress = helper.get_generation_progress()

    assert progress["stage"] == "idle"
    assert progress["current"] == 0
    assert progress["total"] == 0


def test_article_helper_facade_image_helpers_pass_through(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    helper = ArticleHelperFacade(llm_client=_StubLLM())  # type: ignore[arg-type]
    calls = []

    def fake_generate_image_prompts(*args):  # type: ignore[no-untyped-def]
        calls.append(("generate_image_prompts", args))
        return ["prompt-a", "prompt-b"]

    def fake_to_japanese_image_prompt(prompt_text):  # type: ignore[no-untyped-def]
        calls.append(("to_japanese_image_prompt", prompt_text))
        return f"ja:{prompt_text}"

    def fake_to_english_image_prompt(prompt_text):  # type: ignore[no-untyped-def]
        calls.append(("to_english_image_prompt", prompt_text))
        return f"en:{prompt_text}"

    monkeypatch.setattr(helper._generator, "generate_image_prompts", fake_generate_image_prompts)
    monkeypatch.setattr(helper._generator, "to_japanese_image_prompt", fake_to_japanese_image_prompt)
    monkeypatch.setattr(helper._generator, "to_english_image_prompt", fake_to_english_image_prompt)

    prompts = helper.generate_image_prompts([], "user", "title", "lead", "body", 2, "initial_top_candidates")
    prompt_ja = helper.to_japanese_image_prompt("prompt-a")
    prompt_en = helper.to_english_image_prompt("プロンプト")

    assert prompts == ["prompt-a", "prompt-b"]
    assert prompt_ja == "ja:prompt-a"
    assert prompt_en == "en:プロンプト"
    assert calls == [
        ("generate_image_prompts", ([], "user", "title", "lead", "body", 2, "initial_top_candidates")),
        ("to_japanese_image_prompt", "prompt-a"),
        ("to_english_image_prompt", "プロンプト"),
    ]
