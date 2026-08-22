import os
import shutil
import platform
import logging
from contextlib import contextmanager
from selenium import webdriver

SESSION_DIR = "/tmp/chrome_session_tiktok"
IS_WINDOWS = platform.system() == "Windows"

def get_chrome_binary():
    candidates = [
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser"
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

def terminate_lingering_processes():
    try:
        if IS_WINDOWS:
            os.system("taskkill /F /IM chromedriver.exe /T > NUL 2>&1")
            os.system("taskkill /F /IM chrome.exe /T > NUL 2>&1")
        else:
            os.system("pkill -9 -f chromedriver > /dev/null 2>&1")
            os.system("pkill -9 -f chromium > /dev/null 2>&1")
            os.system("pkill -9 -f chrome > /dev/null 2>&1")
    except Exception:
        pass

@contextmanager
def managed_webdriver(user_agent: str, headless: bool = True):
    opts = webdriver.ChromeOptions()
    opts.page_load_strategy = "eager"
    
    if headless:
        opts.add_argument("--headless=new")
        
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-images")
    opts.add_argument("--blink-settings=imagesEnabled=false")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-background-networking")
    opts.add_argument("--renderer-process-limit=1")
    opts.add_argument("--js-flags=--max-old-space-size=256")
    opts.add_argument("--window-size=1440,900")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument(f"--user-agent={user_agent}")
    opts.add_argument("--log-level=3")
    opts.add_argument(f"--user-data-dir={SESSION_DIR}")

    bin_loc = get_chrome_binary()
    if bin_loc:
        opts.binary_location = bin_loc

    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(35)
    driver.set_script_timeout(15)

    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
    except Exception:
        pass

    try:
        yield driver
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        terminate_lingering_processes()
        try:
            shutil.rmtree(SESSION_DIR, ignore_errors=True)
        except Exception:
            pass
