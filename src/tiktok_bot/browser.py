"""Short-lived, resource-constrained Chromium driver."""

from __future__ import annotations

import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from selenium import webdriver


def _chrome_binary() -> str | None:
    for candidate in (
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
    ):
        if Path(candidate).is_file():
            return candidate
    return None


@contextmanager
def managed_webdriver(user_agent: str, headless: bool = True) -> Iterator[webdriver.Chrome]:
    """Start Chromium for one dispatch cycle and release only its resources."""
    with tempfile.TemporaryDirectory(prefix="tiktok-streak-") as profile_dir:
        options = webdriver.ChromeOptions()
        options.page_load_strategy = "eager"
        if headless:
            options.add_argument("--headless=new")

        for argument in (
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-extensions",
            "--disable-background-networking",
            "--disable-sync",
            "--disable-default-apps",
            "--disable-component-update",
            "--disable-features=Translate,MediaRouter",
            "--blink-settings=imagesEnabled=false",
            "--renderer-process-limit=1",
            "--js-flags=--max-old-space-size=256",
            "--window-size=1440,900",
            "--disable-blink-features=AutomationControlled",
            "--log-level=3",
            f"--user-data-dir={profile_dir}",
            f"--user-agent={user_agent}",
        ):
            options.add_argument(argument)

        if binary := _chrome_binary():
            options.binary_location = binary

        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(35)
        driver.set_script_timeout(15)
        try:
            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
            )
            yield driver
        finally:
            driver.quit()
