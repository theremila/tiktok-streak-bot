# TikTok Streak Bot

Lightweight, automated TikTok DM streak maintainer powered by headless Chromium and Selenium.

## Features

- Native support for TikTok's Draft.js rich text editor (`div.public-DraftEditor-content`).
- Flexible recipient resolution with user-defined **Aliases** dictionary (`USER_ALIASES`).
- `eager` page loading strategy avoiding background video buffer hangs.
- Low-memory footprint tuned for minimal 1-core / 1GB RAM VPS nodes (`--disable-images`, single renderer process limit).
- Built-in retry mechanism with DOM state verification after message dispatch.
- Anti-detection CDP evasions (`navigator.webdriver` removal).
- Clean modular package structure (`src/tiktok_bot`).
- Docker Compose and systemd service templates included.

## Project Structure

```text
tiktok-streak-bot/
├── src/
│   └── tiktok_bot/
│       ├── __init__.py      # Package version and metadata
│       ├── __main__.py      # CLI entrypoint & scheduler loop
│       ├── bot.py           # Core StreakBot orchestrator
│       ├── browser.py       # Chrome driver lifecycle & anti-detection
│       ├── config.py        # Settings loader & dataclass schema
│       ├── cookies.py       # Session cookie injection & normalization
│       └── messaging.py     # Draft.js dispatcher & delivery verification
├── scripts/
│   └── setup_vps.sh         # Bare-metal Linux installer
├── deploy/
│   └── tiktok-bot.service   # Systemd service unit
├── data/
│   ├── config.example.json  # Configuration blueprint
│   └── cookies.example.json # Cookie format template
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── main.py                  # Root execution wrapper
```

## Quick Start

### Docker Compose (Recommended)

1. Clone and prepare configuration:

   ```bash
   git clone https://github.com/username/tiktok-streak-bot.git
   cd tiktok-streak-bot
   cp data/config.example.json data/config.json
   ```

2. Export TikTok cookies from your browser (via Cookie-Editor or EditThisCookie) and save as `data/cookies.json`.

3. Launch container:

   ```bash
   docker compose up -d --build
   ```

4. Check logs:

   ```bash
   docker compose logs -f
   ```

### Native Setup

```bash
chmod +x scripts/setup_vps.sh
./scripts/setup_vps.sh
source venv/bin/activate
python main.py
```

## Configuration

Settings are configured via `data/config.json`:

```json
{
  "TEST_MODE": false,
  "TARGET_USERS": [
    "friend_1",
    "friend_2"
  ],
  "USER_ALIASES": {
    "friend_1": ["Display Name 1", "Old Nickname"],
    "friend_2": ["Display Name 2"]
  },
  "MESSAGE_TO_SEND": "Сквирта не существует",
  "TARGET_SEND_TIME_HM": [12, 0],
  "COOKIES_FILE": "cookies.json",
  "LOG_FILENAME": "data/tiktok_bot.txt",
  "HEADLESS_MODE": true
}
```

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `TARGET_USERS` | `array` | List of target usernames or display names. |
| `USER_ALIASES` | `object` | Dictionary mapping a username to alternative nicknames / display names. |
| `MESSAGE_TO_SEND` | `string` | Text to dispatch (supports unicode / emoji). |
| `TARGET_SEND_TIME_HM` | `[hour, min]` | Local schedule trigger time (`[12, 0]` = 12:00 PM). |
| `TEST_MODE` | `boolean` | When `true`, executes immediately on start and exits. |

## License

MIT License.
