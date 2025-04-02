import time
from random import randint
from typing import Literal, Self, Union

import cloudscraper

from .core.logger import logger
from .payload import create_payload_local

scraper = cloudscraper.create_scraper()  # Create a scraper session


class Blum:

    def __init__(self: Self, web_data: str) -> None:
        self.web_data: str = web_data

    @property
    def token(self: Self) -> Union[str, None]:
        if hasattr(self, "_token"):
            return self._token

        response = scraper.post(
            url="https://user-domain.blum.codes/api/v1/auth/provider/PROVIDER_TELEGRAM_MINI_APP",
            json={"query": self.web_data},
        )

        if response.ok:
            if data := response.json():
                self._token: str = data["token"]["access"]

                return self._token

        logger.error(f"User {self.username!r} - Unable to retrieve token!")

        return None

    @property
    def username(self: Self):
        if not hasattr(self, "_username"):
            if me := self.get_me():
                self._username: str = me["username"]

                logger.info(
                    "User {!r} - BP balance is <b>{}{}</b>.".format(
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

    def play_game(self: Self):
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
                f"User {self.username!r} - Game successfully played <b>{game_id!r}<b>."
            )

            logger.success(message)

            return data

        except Exception:
            logger.error(
                f"User {self.username!r} - An error occurred during playing a game!"
            )

    def start_game(self: Self):
        if game := self.play_game():
            self.claim_game(
                game["gameId"],
                int(
                    game["assets"]["CLOVER"]["perClick"],
                ),
            )

    def claim_game(self: Self, game_id: str, multiplier: int):
        try:
            clover = randint(190, 230)
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
                else:
                    logger.warning(f"User {self.username!r} - Unable to claim.")

                logger.info(
                    f"User {self.username!r} - Sleeping about <c>5</c> seconds..."
                )
                time.sleep(5)

                logger.info(
                    "User {!r} - Current BP balance is <b>{}{}</b>.".format(
                        self.username, *self.get_point()
                    )
                )

        except Exception as err:
            logger.error(
                f"User {self.username!r} - Error occurred during claim game: {err}"
            )

    def main(self: Self) -> None:
        if point := self.get_point("PP"):
            play_passes, symbol = point
            logger.info(
                f"User {self.username!r} - Have <b>{play_passes}{symbol}</b> play passes!"
            )

            for num in range(int(play_passes)):
                logger.info(
                    f"User {self.username!r} - Starting new game with this <c>{num!r}</c> number."
                )
                self.start_game()
                logger.info(
                    f"User {self.username!r} - Sleeping about <c>2.5</c> seconds..."
                )
                time.sleep(2.5)


def main() -> None:
    pass


if __name__ == "__main__":
    main()
