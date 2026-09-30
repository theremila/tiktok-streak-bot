"""Configuration loading and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import time
from pathlib import Path
from typing import Any

CONFIG_PATH = Path("data/config.json")
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)
MESSAGES_URL = "https://www.tiktok.com/messages?lang=en"
DEFAULT_MESSAGE = "Сквирта не существует"

@dataclass
class BotConfig:
    test_mode: bool = False
    target_users: tuple[str, ...] = field(default_factory=tuple)
    user_aliases: dict[str, tuple[str, ...]] = field(default_factory=dict)
    message_to_send: str = DEFAULT_MESSAGE
    target_send_time: time = time(12, 0)
    cookies_file: Path = Path("data/cookies.json")
    log_filename: Path = Path("data/tiktok_bot.log")
    user_agent: str = DEFAULT_USER_AGENT
    tiktok_messages_url: str = MESSAGES_URL
    headless_mode: bool = True

    @classmethod
    def load(cls, path: Path | str = CONFIG_PATH) -> "BotConfig":
        config_path = Path(path)
        values = _read_json_object(config_path)
        return cls(
            test_mode=_bool(values.get("TEST_MODE", False), "TEST_MODE"),
            target_users=_unique_users(values.get("TARGET_USERS", [])),
            user_aliases=_aliases(values.get("USER_ALIASES", {})),
            message_to_send=_text(values.get("MESSAGE_TO_SEND")) or DEFAULT_MESSAGE,
            target_send_time=_parse_time(values.get("TARGET_SEND_TIME_HM", [12, 0])),
            cookies_file=_resolve_path(values.get("COOKIES_FILE", "cookies.json"), config_path),
            log_filename=_resolve_path(values.get("LOG_FILENAME", "data/tiktok_bot.log"), config_path),
            user_agent=_text(values.get("USER_AGENT")) or DEFAULT_USER_AGENT,
            tiktok_messages_url=_text(values.get("TIKTOK_MESSAGES_URL")) or MESSAGES_URL,
            headless_mode=_bool(values.get("HEADLESS_MODE", True), "HEADLESS_MODE"),
        )


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        example = path.parent / "config.example.json"
        if example.is_file():
            path = example
        else:
            return {}
    with path.open(encoding="utf-8") as config_file:
        data = json.load(config_file)
    if not isinstance(data, dict):
        raise ValueError("Configuration root must be a JSON object")
    return data


def _parse_time(value: Any) -> time:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError("TARGET_SEND_TIME_HM must be [hour, minute]")
    return time(int(value[0]), int(value[1]))


def _unique_users(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError("TARGET_USERS must be an array")
    users: list[str] = []
    seen: set[str] = set()
    for item in value:
        username = _text(item).strip()
        key = username.casefold()
        if username and key not in seen:
            seen.add(key)
            users.append(username)
    return tuple(users)


def _aliases(value: Any) -> dict[str, tuple[str, ...]]:
    if not isinstance(value, dict):
        raise ValueError("USER_ALIASES must be an object")
    aliases: dict[str, tuple[str, ...]] = {}
    for user, values in value.items():
        username = _text(user).strip()
        if not username or not isinstance(values, list):
            continue
        aliases[username] = tuple(alias for item in values if (alias := _text(item).strip()))
    return aliases


def _resolve_path(value: Any, config_path: Path) -> Path:
    path = Path(_text(value))
    if path.is_absolute():
        return path
    if path.parts and path.parts[0] == "data":
        return path
    return config_path.parent / path


def _bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be true or false")
    return value


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""
