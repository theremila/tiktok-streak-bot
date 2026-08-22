import os
import json
import time
import logging

def inject_cookies(driver, cookie_file: str) -> bool:
    actual_path = cookie_file if os.path.exists(cookie_file) else os.path.join("data", cookie_file)
    if not os.path.exists(actual_path):
        actual_path = "cookies.json"

    if not os.path.exists(actual_path):
        logging.error(f"Cookie file not found: '{cookie_file}'")
        return False

    try:
        with open(actual_path, "r", encoding="utf-8") as f:
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
