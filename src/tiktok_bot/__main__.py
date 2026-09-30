import sys
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta

from .config import BotConfig
from .bot import StreakBot

def setup_logging(log_filename: Path):
    log_filename.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_filename, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    try:
        config = BotConfig.load()
    except (FileNotFoundError, ValueError) as error:
        logging.basicConfig(level=logging.ERROR, format="%(levelname)s - %(message)s")
        logging.error("Invalid bot configuration: %s", error)
        return 2
    setup_logging(config.log_filename)

    bot = StreakBot(config)

    force = "--force" in sys.argv
    if config.test_mode or "--test" in sys.argv or "--oneshot" in sys.argv or force:
        logging.info("Running in immediate execution mode (--oneshot).")
        bot.run_cycle(force=force)
        return

    logging.info(f"Service running in scheduled mode. Daily target: {config.target_send_time.strftime('%H:%M')}")
    last_run_date = None

    while True:
        now = datetime.now()
        current_time = now.time()
        today = now.date()

        window_end = (datetime.combine(today, config.target_send_time) + timedelta(minutes=2)).time()
        in_window = config.target_send_time <= current_time < window_end

        if in_window and today != last_run_date:
            logging.info("Scheduled target window reached. Executing cycle...")
            try:
                bot.run_cycle()
            except Exception as e:
                logging.error(f"Unhandled error in scheduled cycle: {e}")
            finally:
                last_run_date = today
                logging.info(f"Cycle finished. Next scheduled trigger: tomorrow at {config.target_send_time.strftime('%H:%M')}")

        next_run = datetime.combine(today, config.target_send_time)
        if datetime.now() >= next_run:
            next_run += timedelta(days=1)

        secs_until = (next_run - datetime.now()).total_seconds()
        interval = 5 if secs_until < 180 else 60
        time.sleep(interval)

if __name__ == "__main__":
    main()
