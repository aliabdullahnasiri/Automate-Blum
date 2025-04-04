import time
from random import randint
from typing import Dict, List, Literal, Self, Union

import cloudscraper
from rich.console import Console

import config

from .core.logger import logger
from .payload import create_payload_local

scraper = cloudscraper.create_scraper()  # Create a scraper session
console: Console = Console()


class Blum:

    def __init__(self: Self, web_data: str):
        self.web_data: str = web_data

    def login(self: Self, timeout: int = 5):
        try:
            response = scraper.post(
                url="https://user-domain.blum.codes/api/v1/auth/provider/PROVIDER_TELEGRAM_MINI_APP",
                json={"query": self.web_data},
                timeout=25,
            )

            if response.ok:
                if data := response.json():
                    token = data["token"]["access"]
                    return token

        except Exception:
            logger.error(f"Unable to login!")

            if timeout:
                time.sleep(5)
                return self.login(timeout - 1)

    def is_token_valid(self: Self, token: str):
        response = scraper.get(
            "https://user-domain.blum.codes/api/v1/user/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=25,
        )

        return True if response.ok else False

    @property
    def token(self: Self):
        if hasattr(self, "_token") and self.is_token_valid(self._token):
            return self._token

        if token := self.login():
            self._token: str = token

            return self._token

        logger.error(f"User {self.username!r} - Unable to retrieve token!")

        return self.token

    @property
    def username(self: Self):
        if not hasattr(self, "_username"):
            if me := self.get_me():
                self._username: str = me["username"]

                logger.info(
                    "User {!r} - BP balance is <c><b>{}{}</b></c>.".format(
                        self.username, *self.get_point()
                    )
                )

        return self._username

    def get_me(self: Self):
        scraper.options("https://user-domain.blum.codes/api/v1/user/me")
        response = scraper.get(
            "https://user-domain.blum.codes/api/v1/user/me",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=25,
        )

        if response.ok:
            return response.json()

    def get_balance(self: Self):
        response = scraper.get(
            f"https://wallet-domain.blum.codes/api/v1/wallet/my/points/balance",
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=25,
        )

        if response.ok:
            return response.json()

    def get_point(self: Self, symbol: Literal["MP", "BP", "TON", "PP"] = "BP"):
        if balance := self.get_balance():
            points = balance["points"]

            for point in points:
                if point["symbol"] == symbol:
                    return point["balance"], symbol

    def play_game(self: Self, timeout: int = 5):
        response = scraper.post(
            "https://game-domain.blum.codes/api/v2/game/play",
            headers={
                "Authorization": f"Bearer {self.token}",
            },
            timeout=25,
        )

        try:
            data = response.json()

            game_id = data["gameId"]
            message = (
                f"User {self.username!r} - Game successfully played <b>{game_id!r}</b>."
            )

            logger.success(message)

            return data

        except Exception:
            logger.error(
                f"User {self.username!r} - An error occurred during playing a game!"
            )

            if config.DEBUG:
                try:
                    data = response.json()
                    message = data["message"]

                    logger.warning(f"User {self.username!r} - {message}!")
                except Exception:
                    print(response.text)

            logger.info(f"User {self.username!r} - Sleeping about <c>30</c> seconds...")
            time.sleep(30)

            if timeout:
                return self.play_game(timeout - 1)

    def start_game(self: Self):
        if point := self.get_point("PP"):
            play_passes, symbol = point
            play_passes = int(play_passes)
            logger.info(
                f"User {self.username!r} - Have <b>{play_passes}{symbol}</b> play passes!"
            )

            while play_passes:
                if game := self.play_game():
                    if not self.claim_game(
                        game["gameId"],
                        int(
                            game["assets"]["CLOVER"]["perClick"],
                        ),
                    ):
                        continue

                play_passes -= 1

                logger.info(
                    f"User {self.username!r} - Sleeping about <c>2.5</c> seconds..."
                )

                time.sleep(2.5)

    def claim_game(self: Self, game_id: str, multiplier: int):
        claimed: bool = False
        try:
            clover = randint(250, 280)
            bombs = randint(0, 1) if multiplier >= 3 else 0
            points = clover * multiplier - bombs * 100
            freeze = randint(0, 5)
            data = create_payload_local(
                game_id=game_id, clover=clover, freeze=freeze, bombs=bombs
            )

            sleep = 30 + freeze * 3
            logger.info(
                f"User {self.username!r} - Sleeping about <c>{sleep!r}</c> seconds..."
            )
            time.sleep(sleep)

            response = scraper.post(
                "https://game-domain.blum.codes/api/v2/game/claim",
                json={"payload": data},
                headers={
                    "Authorization": f"Bearer {self.token}",
                },
                timeout=25,
            )

            if response.ok:
                if response.text == "OK":
                    logger.success(
                        f"User {self.username!r} - Points <b>{points!r}</b> are successfully claimed."
                    )

                    claimed = True
                else:
                    logger.warning(f"User {self.username!r} - Unable to claim.")

                logger.info(
                    f"User {self.username!r} - Sleeping about <c>5</c> seconds..."
                )
                time.sleep(5)

                logger.info(
                    "User {!r} - Current BP balance is <c><b>{}{}</b></c>.".format(
                        self.username, *self.get_point()
                    )
                )

        except Exception as err:
            logger.error(
                f"User {self.username!r} - Error occurred during claim game: {err}"
            )

        return claimed

    def get_tasks(
        self: Self,
        status: Union[
            Literal[
                "READY_FOR_VERIFY",
                "READY_FOR_CLAIM",
                "FINISHED",
                "NOT_STARTED",
                "STARTED",
            ],
            None,
        ] = None,
        validation_type: Union[Literal["DEFAULT", "KEYWORD"], None] = None,
    ):
        try:
            response = scraper.get(
                "https://earn-domain.blum.codes/api/v1/tasks",
                headers={
                    "Authorization": f"Bearer {self.token}",
                },
                timeout=25,
            )

            if response.ok:
                __tasks__: List = []
                tasks = []

                for section in response.json():
                    tasks.extend(section["tasks"])
                    tasks.extend(section["subSections"])

                for task in tasks:
                    try:
                        __tasks__.extend(task["tasks"])
                    except Exception:
                        __tasks__.append(task)

                return [
                    i
                    for i in filter(
                        lambda item: (
                            item["status"] == status if status is not None else True
                        )
                        and (
                            item["validationType"] == validation_type
                            if validation_type is not None
                            else True
                        ),
                        __tasks__,
                    )
                ]
        except Exception as err:
            if config.DEBUG:
                console.print(err)

    def start_task(self: Self, identity: str):
        try:
            response = scraper.post(
                f"https://earn-domain.blum.codes/api/v1/tasks/{identity}/start",
                headers={
                    "Authorization": f"Bearer {self.token}",
                },
                timeout=25,
            )

            if config.DEBUG:
                console.print(response.text)

            if response.ok:
                logger.success(f"User {self.username!r} - Task successfully started.")

                return response.json()

        except Exception:
            logger.error(
                f"User {self.username!r} - An error occurred during starting the task!"
            )

    def validate_task(self: Self, identity: str, data: Union[Dict, None] = None):
        try:
            kwargs: Dict = {
                "headers": {
                    "Authorization": f"Bearer {self.token}",
                },
                "timeout": 25,
            }

            if data:
                kwargs.setdefault("json", data)

            response = scraper.post(
                f"https://earn-domain.blum.codes/api/v1/tasks/{identity}/validate",
                **kwargs,
            )

            if config.DEBUG:
                console.print(response.text)

            if response.ok:
                logger.success(f"User {self.username!r} - Task successfully validated.")

                return response.json()

        except Exception:
            logger.error(
                f"User {self.username} - An error occurred during validating the task!"
            )

    def claim_task(self: Self, identity: str):
        try:
            response = scraper.post(
                f"https://earn-domain.blum.codes/api/v1/tasks/{identity}/claim",
                headers={
                    "Authorization": f"Bearer {self.token}",
                },
                timeout=25,
            )

            if config.DEBUG:
                console.print(response.text)

            if response.ok:
                logger.success(f"User {self.username!r} - Task successfully claimed.")

                return True

        except Exception:
            logger.error(
                f"User {self.username} - An error occurred during claiming the task!"
            )

    def complete_tasks(self: Self):

        if tasks := self.get_tasks():
            for task in tasks:
                identity = task["id"]
                status = task["status"]
                validation_type = task["validationType"]

                if status == "FINISHED":
                    continue

                self.start_task(identity)

                if validation_type == "KEYWORD":
                    for value in (
                        scraper.get(config.KEYWORDS_URL, timeout=25).json().values()
                    ):
                        keyword = value["keyword"]
                        if self.validate_task(identity, {"keyword": keyword}):
                            break
                else:
                    self.validate_task(identity)

                self.claim_task(identity)

    def main(self: Self):
        if config.PLAY_GAME:
            self.start_game()

        if config.COMPLETE_TASKS:
            self.complete_tasks()


def main():
    pass


if __name__ == "__main__":
    main()
