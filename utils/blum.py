import time
from random import randint
from typing import Literal, Self

import cloudscraper

import config

from .core.logger import logger
from .payload import create_payload_local

scraper = cloudscraper.create_scraper()  # Create a scraper session


class Blum:

    def __init__(self: Self, web_data: str):
        self.web_data: str = web_data

    def login(self: Self, timeout: int = 5):
        try:
            response = scraper.post(
                url="https://user-domain.blum.codes/api/v1/auth/provider/PROVIDER_TELEGRAM_MINI_APP",
                json={"query": self.web_data},
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
        )

        return True if response.ok else False

    @property
    def token(self: Self):
        if hasattr(self, "_token") and self.is_token_valid(self._token):
            return self._token

        if token := self.login():
            self._token = token

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
        )

        if response.ok:
            return response.json()

    def get_balance(self: Self):
        response = scraper.get(
            f"https://wallet-domain.blum.codes/api/v1/wallet/my/points/balance",
            headers={"Authorization": f"Bearer {self.token}"},
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
        if game := self.play_game():
            if self.claim_game(
                game["gameId"],
                int(
                    game["assets"]["CLOVER"]["perClick"],
                ),
            ):
                return True

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

    def main(self: Self):
        if point := self.get_point("PP"):
            play_passes, symbol = point
            play_passes = int(play_passes)
            logger.info(
                f"User {self.username!r} - Have <b>{play_passes}{symbol}</b> play passes!"
            )

            while play_passes:
                if not self.start_game():
                    continue

                play_passes -= 1

                logger.info(
                    f"User {self.username!r} - Sleeping about <c>2.5</c> seconds..."
                )

                time.sleep(2.5)


def main():
    pass


if __name__ == "__main__":
    main()
