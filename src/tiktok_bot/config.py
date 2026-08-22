import os
import json
import logging
from dataclasses import dataclass, field
from datetime import time as dt_time
from typing import List, Dict

DEFAULT_CONFIG_PATH = "data/config.json"

DEFAULT_CONFIG = {
    "TEST_MODE": False,
    "TARGET_USERS": [
        "FriendUsername1",
        "FriendUsername2"
    ],
    "USER_ALIASES": {
        "FriendUsername1": ["Nickname1", "Display Name 1"]
    },
    "MESSAGE_TO_SEND": "Сквирта не существует",
    "TARGET_SEND_TIME_HM": [12, 0],
    "COOKIES_FILE": "cookies.json",
    "LOG_FILENAME": "data/tiktok_bot.txt",
    "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "TIKTOK_MESSAGES_URL": "https://www.tiktok.com/messages?lang=en",
    "HEADLESS_MODE": True
}

@dataclass
class BotConfig:
    test_mode: bool = False
    target_users: List[str] = field(default_factory=lambda: ["FriendUsername1", "FriendUsername2"])
    user_aliases: Dict[str, List[str]] = field(default_factory=dict)
    message_to_send: str = "Сквирта не существует"
    target_send_time: dt_time = field(default_factory=lambda: dt_time(12, 0))
    cookies_file: str = "cookies.json"
    log_filename: str = "data/tiktok_bot.txt"
    user_agent: str = DEFAULT_CONFIG["USER_AGENT"]
    tiktok_messages_url: str = DEFAULT_CONFIG["TIKTOK_MESSAGES_URL"]
    headless_mode: bool = True

    @classmethod
    def load(cls, filepath: str = DEFAULT_CONFIG_PATH) -> "BotConfig":
        data = DEFAULT_CONFIG.copy()
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    data.update(loaded)
            except Exception as e:
                logging.warning(f"Could not read config at '{filepath}': {e}. Using defaults.")
        else:
            try:
                os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
            except Exception:
                pass

        time_hm = data.get("TARGET_SEND_TIME_HM", [12, 0])
        try:
            target_time = dt_time(int(time_hm[0]), int(time_hm[1]))
        except Exception:
            target_time = dt_time(12, 0)

        return cls(
            test_mode=data.get("TEST_MODE", False),
            target_users=data.get("TARGET_USERS", DEFAULT_CONFIG["TARGET_USERS"]),
            user_aliases=data.get("USER_ALIASES", {}),
            message_to_send=data.get("MESSAGE_TO_SEND", DEFAULT_CONFIG["MESSAGE_TO_SEND"]),
            target_send_time=target_time,
            cookies_file=data.get("COOKIES_FILE", DEFAULT_CONFIG["COOKIES_FILE"]),
            log_filename=data.get("LOG_FILENAME", DEFAULT_CONFIG["LOG_FILENAME"]),
            user_agent=data.get("USER_AGENT", DEFAULT_CONFIG["USER_AGENT"]),
            tiktok_messages_url=data.get("TIKTOK_MESSAGES_URL", DEFAULT_CONFIG["TIKTOK_MESSAGES_URL"]),
            headless_mode=data.get("HEADLESS_MODE", True)
        )
