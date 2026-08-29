import json
import time
import logging
from pathlib import Path

def inject_cookies(driver, cookie_file: Path) -> bool:
    if not cookie_file.is_file():
        logging.error("Cookie file not found: '%s'", cookie_file)
        return False

    try:
        with cookie_file.open("r", encoding="utf-8") as f:
            cookies = json.load(f)

        driver.get("https://www.tiktok.com/explore")
        time.sleep(1.5)

        added = 0
        for cookie in cookies:
            try:
                c = {
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "domain": cookie.get("domain", ".tiktok.com"),
                    "path": cookie.get("path", "/")
                }
                if "secure" in cookie:
                    c["secure"] = cookie["secure"]
                driver.add_cookie(c)
                added += 1
            except Exception:
                pass

        logging.info(f"Successfully injected {added} cookies into session.")
        return added > 0
    except Exception as e:
        logging.error(f"Failed to parse and inject cookies: {e}")
        return False
