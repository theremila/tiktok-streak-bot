import time
import random
import logging
from typing import Optional

from .config import BotConfig
from .browser import managed_webdriver
from .cookies import inject_cookies
from .messaging import find_and_open_chat, dispatch_message

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

class StreakBot:
    def __init__(self, config: Optional[BotConfig] = None):
        self.config = config or BotConfig.load()

    def run_cycle(self) -> int:
        logging.info("=== Starting TikTok Streak Dispatch Cycle ===")
        success_count = 0

        try:
            with managed_webdriver(user_agent=self.config.user_agent, headless=self.config.headless_mode) as driver:
                logging.info("Browser instance initialized.")

                if not inject_cookies(driver, self.config.cookies_file):
                    raise RuntimeError("Failed to load and inject session cookies.")

                logging.info(f"Navigating to {self.config.tiktok_messages_url}...")
                driver.get(self.config.tiktok_messages_url)
                time.sleep(random.uniform(3.0, 5.0))

                if not self.config.target_users:
                    logging.error("No target users configured.")
                    return 0

                # Deduplicate recipients
                seen = set()
                targets = []
                for u in self.config.target_users:
                    norm = u.lower().strip()
                    if norm not in seen:
                        seen.add(norm)
                        targets.append(u)

                logging.info(f"Targeting {len(targets)} recipient(s): {', '.join(targets)}")

                for user in targets:
                    safe_user = "".join(c for c in user if c.isprintable())
                    aliases = self.config.user_aliases.get(user, [])
                    sent = False

                    for attempt in range(1, MAX_RETRIES + 1):
                        logging.info(f"--- Recipient: '{safe_user}' (attempt {attempt}/{MAX_RETRIES}) ---")

                        if attempt > 1:
                            try:
                                driver.get(self.config.tiktok_messages_url)
                                time.sleep(2.5)
                            except Exception:
                                pass

                        if not find_and_open_chat(driver, user, aliases=aliases):
                            logging.warning(f"✗ Conversation not found for '{safe_user}'.")
                            if attempt < MAX_RETRIES:
                                time.sleep(RETRY_DELAY_SECONDS)
                            continue

                        if dispatch_message(driver, self.config.message_to_send):
                            sent = True
                            break

                        logging.warning(f"✗ Message dispatch failed for '{safe_user}'.")
                        if attempt < MAX_RETRIES:
                            time.sleep(RETRY_DELAY_SECONDS)

                    if sent:
                        success_count += 1
                        logging.info(f"✓ Message delivered to '{safe_user}'.")
                    else:
                        logging.error(f"✗ Delivery failed for '{safe_user}'.")

                    if len(targets) > 1 and user != targets[-1]:
                        wait = random.uniform(2.5, 4.5)
                        time.sleep(wait)

                logging.info(f"=== Streak Cycle Finished: {success_count}/{len(targets)} messages delivered ===")
                return success_count

        except Exception as e:
            logging.error(f"Critical error during streak cycle: {e}")
            return success_count
