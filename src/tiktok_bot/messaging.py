import time
import random
import logging
from typing import List, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CONVERSATION_ITEM_XPATH = "//*[@data-e2e='dm-new-conversation-item']"
EDITOR_CSS_SELECTOR     = "div.public-DraftEditor-content, div[role='textbox'], div[contenteditable='true']"

def find_and_open_chat(driver, target_name: str, aliases: Optional[List[str]] = None) -> bool:
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, CONVERSATION_ITEM_XPATH))
        )
        time.sleep(1.0)

        items = driver.find_elements(By.XPATH, CONVERSATION_ITEM_XPATH)
        if not items:
            return False

        search_keys = [target_name.lower().strip()]
        if aliases:
            for alias in aliases:
                norm_alias = alias.lower().strip()
                if norm_alias and norm_alias not in search_keys:
                    search_keys.append(norm_alias)

        for i, item in enumerate(items):
            try:
                raw_text = item.text.strip().lower()
                tags = [t.text.strip().lower() for t in item.find_elements(By.XPATH, ".//p | .//span") if t.text.strip()]

                matched = False
                for key in search_keys:
                    if tags and tags[0] == key:
                        matched = True
                        break
                    if key in raw_text:
                        matched = True
                        break

                if matched:
                    logging.info(f"Matched '{target_name}' at dialog position #{i+1}. Opening chat...")
                    driver.execute_script("arguments[0].scrollIntoView(true);", item)
                    time.sleep(0.3)
                    item.click()
                    time.sleep(random.uniform(2.0, 3.0))
                    return True
            except Exception:
                continue

        return False
    except Exception as e:
        logging.error(f"Error locating conversation for '{target_name}': {e}")
        return False

def dispatch_message(driver, message_text: str) -> bool:
    try:
        editor = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, EDITOR_CSS_SELECTOR))
        )

        try:
            editor.click()
            time.sleep(0.3)
        except Exception:
            driver.execute_script("arguments[0].focus();", editor)

        if any(ord(c) > 0xffff for c in message_text):
            driver.execute_script(
                "arguments[0].focus(); "
                "arguments[0].innerText = arguments[1]; "
                "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
                editor, message_text
            )
        else:
            editor.send_keys(message_text)

        time.sleep(random.uniform(0.6, 1.0))
        editor.send_keys(Keys.ENTER)
        time.sleep(random.uniform(2.0, 3.0))

        remaining = (editor.text or "").strip()
        if remaining == "" or remaining != message_text.strip():
            return True
        else:
            return False
    except Exception as e:
        logging.error(f"Error dispatching message in open chat: {e}")
        return False
