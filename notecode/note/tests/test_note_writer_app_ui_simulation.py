from __future__ import annotations

import time

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from nicegui.testing import Screen


pytest_plugins = ("nicegui.testing.plugin",)


def _find_visible_input(screen, aria_label: str):
    deadline = time.time() + 8
    while time.time() < deadline:
        for element in screen.selenium.find_elements(By.CSS_SELECTOR, f'input[aria-label="{aria_label}"]'):
            try:
                if element.is_displayed():
                    return element
            except Exception:
                continue
        screen.wait(0.1)
    raise AssertionError(f'visible input not found: {aria_label}')


def _visible_button_count(screen, text: str) -> int:
    buttons = screen.selenium.find_elements(By.XPATH, f'//button[normalize-space()="{text}"]')
    return sum(1 for button in buttons if button.is_displayed())


def _click_last_visible_button(screen, text: str) -> None:
    buttons = screen.selenium.find_elements(By.XPATH, f'//button[normalize-space()="{text}"]')
    visible_buttons = [button for button in buttons if button.is_displayed()]
    if not visible_buttons:
        raise AssertionError(f'visible button not found: {text}')
    visible_buttons[-1].click()


def _replace_visible_input_value(screen, aria_label: str, value: str):
    element = _find_visible_input(screen, aria_label)
    element.click()
    element.send_keys(Keys.CONTROL, "a")
    element.send_keys(Keys.BACKSPACE)
    screen.wait_for(lambda: element.get_attribute("value") == "")
    if value:
        element.send_keys(value)
        screen.wait_for(lambda: element.get_attribute("value") == value)
    return element


@pytest.mark.nicegui_main_file("note/note_writer_app.py")
def test_audience_field_does_not_auto_commit_while_typing(screen, monkeypatch, caplog) -> None:
    monkeypatch.setenv("PORT", str(Screen.PORT))
    monkeypatch.setenv("HEADLESS", "1")
    screen.open("/", timeout=20.0)
    screen.should_contain("STEP3 読者")

    audience_input = _find_visible_input(screen, "主な読者")
    assert audience_input.get_attribute("value") == "一般読者"

    audience_input = _replace_visible_input_value(screen, "主な読者", "導")
    screen.wait(0.2)

    assert audience_input.get_attribute("value") == "導"
    assert _visible_button_count(screen, "修正") == 0

    audience_input.send_keys("入")
    screen.wait(0.2)

    assert audience_input.get_attribute("value") == "導入"
    assert _visible_button_count(screen, "修正") == 0
    screen.should_contain("STEP3 読者")
    screen.should_not_contain("STEP4 書き手")
    caplog.clear()


@pytest.mark.nicegui_main_file("note/note_writer_app.py")
def test_audience_field_advances_only_after_explicit_next(screen, monkeypatch, caplog) -> None:
    monkeypatch.setenv("PORT", str(Screen.PORT))
    monkeypatch.setenv("HEADLESS", "1")
    screen.open("/", timeout=20.0)
    screen.should_contain("STEP3 読者")

    audience_input = _replace_visible_input_value(screen, "主な読者", "導入検討中の担当者")

    assert _visible_button_count(screen, "修正") == 0

    _click_last_visible_button(screen, "次へ")
    screen.wait_for(lambda: _visible_button_count(screen, "修正") >= 1)

    assert _visible_button_count(screen, "修正") >= 1
    screen.should_contain("STEP4 書き手")
    caplog.clear()


@pytest.mark.nicegui_main_file("note/note_writer_app.py")
def test_enter_in_audience_field_does_not_trigger_next(screen, monkeypatch, caplog) -> None:
    monkeypatch.setenv("PORT", str(Screen.PORT))
    monkeypatch.setenv("HEADLESS", "1")
    screen.open("/", timeout=20.0)
    screen.should_contain("STEP3 読者")

    audience_input = _replace_visible_input_value(screen, "主な読者", "導入検討中")
    audience_input.send_keys(Keys.ENTER)
    screen.wait(0.3)

    assert audience_input.get_attribute("value") == "導入検討中"
    assert _visible_button_count(screen, "修正") == 0
    screen.should_not_contain("STEP4 書き手")
    caplog.clear()
