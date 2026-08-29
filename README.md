# TikTok Streak Bot

Small scheduled TikTok DM sender. It keeps only the Python scheduler alive while
waiting; Chromium starts for a dispatch cycle and is closed immediately after it.

## Behaviour

- Uses one short-lived, headless Chromium instance per cycle.
- Creates an isolated temporary browser profile and removes it on exit.
- Leaves unrelated Chrome and ChromeDriver processes untouched.
- Injects an exported TikTok cookie session and sends a message to each configured recipient.
- Runs once with `--test`; otherwise it waits for the daily configured time.

The idle container is intentionally lightweight. Browser memory is needed only while
TikTok is open; it cannot be reduced to the idle footprint without replacing the
browser-based automation approach.

## Run with Docker Compose

```bash
git clone https://github.com/evaware-dev/tiktok-streak-bot.git
cd tiktok-streak-bot
cp data/config.example.json data/config.json
# Export your own TikTok cookies to data/cookies.json.
docker compose up -d --build
docker compose logs -f
```

The service runs in the timezone configured by `TZ` in
[docker-compose.yml](docker-compose.yml). Set it to the intended local timezone
before starting the container.

To run a single cycle deliberately:

```bash
docker compose run --rm tiktok-streak-bot python -u main.py --test
```

Stop the scheduler with `docker compose down`. Cookie files and local configuration
are intentionally not committed.

## Remote install and removal

The scripts run from your own computer and deploy through SSH. They accept command
line arguments and prompt only for missing values. For password authentication,
either enter it without echoing or provide `TIKTOK_BOT_SSH_PASSWORD`; SSH keys work
without `sshpass`.

```bash
scripts/install --host 203.0.113.10 --port 22 --user root \
  --timezone Europe/Kaliningrad

scripts/uninstall --host 203.0.113.10 --port 22 --user root
```

The same values can be supplied with `TIKTOK_BOT_SSH_HOST`,
`TIKTOK_BOT_SSH_PORT`, `TIKTOK_BOT_SSH_USER`, `TIKTOK_BOT_SSH_PASSWORD`,
`TIKTOK_BOT_DESTINATION`, and `TIKTOK_BOT_TIMEZONE`.

`install` preserves `data/config.json` and `data/cookies.json` already present on
the server and copies timestamped backups into `backups/`. On a fresh server it
creates both files from the safe examples before starting Docker. On Debian and
Ubuntu, it installs Docker Engine and the Compose plugin when they are missing; the
remote account must therefore be `root` or have passwordless/interactive `sudo`.
`uninstall` stops the bot but deliberately retains its directory and private data.
Use `--purge` only when the whole remote installation should be deleted.

## Configuration

Create `data/config.json` from [data/config.example.json](data/config.example.json):

```json
{
  "TARGET_USERS": ["friend_1", "friend_2"],
  "USER_ALIASES": {
    "friend_1": ["Display Name 1"]
  },
  "MESSAGE_TO_SEND": "Сквирта не существует",
  "TARGET_SEND_TIME_HM": [12, 0],
  "COOKIES_FILE": "cookies.json",
  "LOG_FILENAME": "data/tiktok_bot.log",
  "HEADLESS_MODE": true
}
```

`TARGET_SEND_TIME_HM` is `[hour, minute]` in the container timezone. A recipient
is sent to once per cycle even if it appears multiple times in `TARGET_USERS`.
`USER_ALIASES` supplies alternative names when TikTok's UI does not expose the
username directly. `TEST_MODE: true` has the same one-shot behaviour as `--test`.

The application fails clearly when the configuration file is absent or malformed;
it never writes a replacement file with placeholder users.

## Layout

- [src/tiktok_bot](src/tiktok_bot) — configuration, scheduler, browser lifecycle, and TikTok UI actions.
- [data](data) — configuration and cookie templates.
- [Dockerfile](Dockerfile) and [docker-compose.yml](docker-compose.yml) — the supported deployment.

## License

MIT License. See [LICENSE](LICENSE).
