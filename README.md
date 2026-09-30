# TikTok Streak Bot

Automated TikTok streak keeper and message dispatcher using TikTok's Protobuf API.

## Behaviour

- Queries streak status, expiration countdowns, and restorable state from `/tiktok/v1/im/streaks/get`.
- Sends configured streak messages via `/v1/message/send` when an active streak requires maintenance.
- Automatically restores lost streaks via `/tiktok/v1/im/streaks/restore` if streak restores are available.
- Evaluates pending actions once and exits with `--oneshot`; runs a continuous daily scheduler otherwise.
- Dispatches configured messages immediately to all streak contacts when invoked with `--force`.
- Keeps session tokens in memory during execution without writing credentials to `.env` files.

## Run with Docker Compose

```bash
git clone https://github.com/theremila/tiktok-streak-bot.git
cd tiktok-streak-bot
cp data/config.example.json data/config.json
# Export your TikTok cookies into data/cookies.json
docker compose up -d --build
```

The service runs in the timezone configured by `TZ` in [docker-compose.yml](docker-compose.yml). Set it to the intended local timezone before starting the container.

To run a single cycle deliberately:

```bash
docker compose run --rm tiktok-streak-bot python -u main.py --oneshot
```

To force-send a streak message to all active streak contacts immediately:

```bash
docker compose run --rm tiktok-streak-bot python -u main.py --force
```

Stop the scheduler with `docker compose down`.

## TikTok session cookies

The bot authenticates using an exported TikTok browser session and does not need account passwords. Because `data/cookies.json` grants direct session access: never commit it, publish it, or send it to anyone.

1. Open `https://www.tiktok.com/messages?lang=en` in a desktop browser and ensure conversations load.
2. Export the full TikTok cookie set as a JSON array using an extension such as Cookie-Editor.
3. Save the exported JSON array to `data/cookies.json`.

The bot extracts `sessionid`, `msToken`, `ttwid`, and verification tokens directly from this file. When TikTok expires the session, export a new cookie set and replace `data/cookies.json`.

## Remote install and removal

The scripts run from your local machine and deploy over SSH:

```bash
scripts/install --host 203.0.113.10 --port 22 --user root --timezone Europe/Kaliningrad
scripts/uninstall --host 203.0.113.10 --port 22 --user root
```

Parameters can also be supplied via environment variables: `TIKTOK_BOT_SSH_HOST`, `TIKTOK_BOT_SSH_PORT`, `TIKTOK_BOT_SSH_USER`, `TIKTOK_BOT_SSH_PASSWORD`, `TIKTOK_BOT_DESTINATION`, and `TIKTOK_BOT_TIMEZONE`.

Existing `data/config.json` and `data/cookies.json` files on the server are preserved across updates and backed up into `backups/`. `uninstall` stops the bot but retains private data. Use `--purge` to delete the remote installation directory entirely.

## Configuration

Create `data/config.json` from [data/config.example.json](data/config.example.json):

```json
{
  "MESSAGE_TO_SEND": "🔥",
  "TARGET_SEND_TIME_HM": [12, 0],
  "COOKIES_FILE": "cookies.json",
  "LOG_FILENAME": "data/tiktok_bot.log",
  "TEST_MODE": false
}
```

- `MESSAGE_TO_SEND`: message text sent to maintain active streaks.
- `TARGET_SEND_TIME_HM`: `[hour, minute]` scheduled trigger time in the container timezone.
- `COOKIES_FILE`: path to the cookie file relative to `data/` or the project root.
- `LOG_FILENAME`: destination log file path.
- `TEST_MODE`: when set to `true`, executes a single cycle and exits immediately.

## License

MIT License. See [LICENSE](LICENSE).
