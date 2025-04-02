import asyncio

from rich.console import Console
from rich.traceback import install

from utils.blum import Blum
from utils.core.telegram import Telegram

install()

console: Console = Console()
telegram: Telegram = Telegram()

if web_data := asyncio.run(telegram.get_web_data("BlumCryptoBot", "app")):
    for data in web_data:
        blum: Blum = Blum(data)
        blum.main()
