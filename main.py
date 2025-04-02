import asyncio
import threading
from typing import List

from rich.console import Console
from rich.traceback import install

from utils.blum import Blum
from utils.core.telegram import Telegram

install()

console: Console = Console()
telegram: Telegram = Telegram()

if web_data := asyncio.run(telegram.get_web_data("BlumCryptoBot", "app")):
    threads: List[threading.Thread] = []

    for data in web_data:
        blum: Blum = Blum(data)
        threads.append(threading.Thread(target=blum.start_game))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()
