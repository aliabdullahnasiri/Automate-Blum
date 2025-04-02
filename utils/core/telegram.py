import os
from typing import Dict, List, Self, Union
from urllib.parse import unquote

import requests
from rich.console import Console
from rich.traceback import install
from telethon.sessions import StringSession
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import RequestAppWebViewRequest
from telethon.tl.types import InputBotAppShortName, InputPeerUser, InputUser

from config import DEBUG

from .logger import logger

install()

console: Console = Console()


class Telegram(object):

    @staticmethod
    def get_sessions() -> Union[List[Dict[str, Union[str, int]]], None]:
        try:
            if URL := os.getenv("SESS_URL"):
                response: requests.Response = requests.get(URL)

                if response.ok:
                    logger.success("Sessions successfully retrieved.")
                    return response.json()

        except Exception:
            logger.error("Unable to retrieve sessions!")

        return None

    @property
    async def clients(self) -> List[TelegramClient]:
        clients: List[TelegramClient] = []

        if sessions := Telegram.get_sessions():
            for session in sessions:
                try:
                    client: TelegramClient = TelegramClient(
                        StringSession(session["session_string"]),
                        session["api_id"],
                        session["api_hash"],
                    )

                    async with client:
                        me = await client.get_me()
                        username = me.username

                        logger.success(f"The client {username!r} is valid.")

                    clients.append(client)
                except Exception as err:
                    logger.warning(f"The session {session['api_id']!r} is not valid!")

                    if DEBUG:
                        console.print(err)

        return clients

    async def get_web_data(
        self: Self,
        bot_username: str,
        bot_shortname: str,
        start_param: Union[str, None] = None,
    ) -> List[str]:
        data: List[str] = []

        for client in await self.clients:
            async with client:
                await client.get_me()
                bot = await client.get_entity(bot_username)
                peer = InputPeerUser(bot.id, bot.access_hash)
                app = InputBotAppShortName(
                    bot_id=InputUser(
                        user_id=peer.user_id,
                        access_hash=peer.access_hash,
                    ),
                    short_name=bot_shortname,
                )

                web_view = await client(
                    RequestAppWebViewRequest(
                        peer=peer,
                        app=app,
                        platform="android",
                        write_allowed=True,
                        start_param=start_param,
                    )
                )
                webview_url = web_view.url

                tg_web_data = unquote(
                    string=webview_url.split("tgWebAppData=")[1].split(
                        "&tgWebAppVersion"
                    )[0]
                )
                data.append(tg_web_data)

        return data


def main() -> None:
    pass


if __name__ == "__main__":
    main()
