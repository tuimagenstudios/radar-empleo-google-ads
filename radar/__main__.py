"""Uso: python -m radar [--dry-run] [--config config.yaml] (RF-EJE-01, RF-EJE-02)."""

from __future__ import annotations

import argparse
import logging
import os
import sys

from dotenv import load_dotenv

from radar.collectors import build_collectors
from radar.config import ConfigError, load_config
from radar.notifier import ConsoleNotifier, TelegramNotifier
from radar.pipeline import run
from radar.storage import Storage


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="radar", description="Radar de Empleo · Google Ads")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--dry-run", action="store_true",
                        help="hace todo menos enviar a Telegram y escribir en la base")
    args = parser.parse_args(argv)

    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")  # emojis en la consola de Windows
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    load_dotenv()

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"Error de configuración: {exc}", file=sys.stderr)
        return 2

    if args.dry_run:
        notifier = ConsoleNotifier()
    else:
        token, chat_id = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
        if not token or not chat_id:
            print("Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID (ver .env.example).",
                  file=sys.stderr)
            return 2
        notifier = TelegramNotifier(token, chat_id)

    storage = Storage.open(config.ruta(config.base_de_datos), dry_run=args.dry_run)
    try:
        r = run(config, build_collectors(config), storage, notifier)
    finally:
        storage.close()
    logging.info("Leídas %d · nuevas %d · duplicadas %d · notificadas %d · errores %d",
                 r.leidas, len(r.nuevas), r.duplicadas, len(r.a_notificar), len(r.errores))
    return 1 if r.errores and not r.leidas else 0


if __name__ == "__main__":
    sys.exit(main())
