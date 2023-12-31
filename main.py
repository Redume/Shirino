#!/usr/bin/env python3

import asyncio
import hashlib
import json
import logging
import re

import string
from typing import List, Any, Dict, Optional

import requests
from aiogram import Dispatcher, types, Bot
import aiohttp.client_exceptions
from pydantic.v1 import BaseSettings
from selenium.webdriver.common.actions import interaction

# Constants
DDG_URL = 'https://duckduckgo.com/js/spice/currency'
COINAPI_URL = 'https://rest.coinapi.io/v1/exchangerate'


# ---


# Config from .env
class Settings(BaseSettings):
    debug: bool
    timeout: int = 2
    ndigits: int = 3
    coinapi_keys: List[str]
    telegram_token: str

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()  # type: ignore
# ---


# Logging
log = logging.getLogger('shirino')
handler = logging.StreamHandler()
fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

handler.setFormatter(fmt)
log.addHandler(handler)

if settings.debug:
    handler.setLevel(logging.DEBUG)
    log.setLevel(logging.DEBUG)
# ---


coinapi_len = len(settings.coinapi_keys)
coinapi_active = [0]  # API key index
dp = Dispatcher()


class CurrencyConverter:

    def __init__(self) -> None:

        self.amount: float = 1.0
        self.conv_amount: float = 0.0
        self.from_currency = ''
        self.conv_currency = ''

    def convert(self) -> None:
        """Currency conversion"""

        if not self.ddgapi():
            self.coinapi()

        str_amount = f'{self.conv_amount}'
        point = str_amount.find(".")
        after_point = str_amount[point + 1:]

        fnz = min(  # index of first non-zero digit
            (
                after_point.index(i)
                for i in string.digits[1:]
                if i in after_point
            ),
            default=-1,
        )

        if fnz == -1:
            # it is an integer like 81.0
            return

        # how many digits should be after the point:
        # ndigits (3 by default) after first non-zero
        ndigits = fnz + settings.ndigits

        self.conv_amount = round(self.conv_amount, ndigits)

    def ddgapi(self) -> bool:
        """Получение данных фиатной валюты через DuckDuckGo

        e.g: https://duckduckgo.com/js/spice/currency/1/USD/RUB

        Returns:
            `False` если валюты нет в API
            `True` если конвертация прошла успешно
        """

        # Запрос к API
        res = requests.get(f'{DDG_URL}/{self.amount}/{self.from_currency}/{self.conv_currency}')
        data: Dict[str, Any] = json.loads(re.findall(r'(.+)\);', res.text)[0])

        log.debug(data)

        if len(data.get('to')) == 0:
            return False

        conv: Dict[str, str] = data.get('to')[0]
        conv_amount = conv.get("mid")

        if conv_amount is None:
            raise RuntimeError('Ошибка при конвертации валюты через DuckDuckGo')

        log.debug(conv)
        log.debug(conv_amount)

        self.conv_amount = float(conv_amount)

        return True

    def coinapi(self, depth: int = coinapi_len) -> None:
        """Получение данных с CoinAPI для получения курса криптовалюты

        Args:
            depth (int, optional): Счетчик, защищающий от рекурсии
        """

        if depth <= 0:
            raise RecursionError('Рейтлимит на всех токенах')

        resp = requests.get(
            (
                f'{COINAPI_URL}/{self.from_currency}'
                f'/{self.conv_currency}'
            ),
            headers={
                'X-CoinAPI-Key': settings.coinapi_keys[coinapi_active[0]],
            },
            timeout=settings.timeout,
        )

        if resp.status_code == 429:
            log.warning('CoinAPI ratelimited, rotating token')
            rotate_token(settings.coinapi_keys, coinapi_active)
            self.coinapi(depth - 1)

        data: Dict[str, Any] = resp.json()
        rate = data.get('rate')
        if rate is None:
            raise RuntimeError('Не удалось получить курс валюты от CoinAPI')
        self.conv_amount = float(rate * self.amount)


def rotate_token(lst: List[str], active: List[int]) -> None:
    """Смена API-ключей CoinAPI при ratelimits

    Args:
        lst (List[str]): Список ключей
        active (List[str]): Изменяемый объект с текущим ключевым индексом
    """

    active[0] = (active[0] + 1) % len(lst)


async def inline_reply(result_id: str, title: str, description: str or None, inline_query: types.InlineQuery) -> None:
    article: List[Optional[types.InlineQueryResultArticle]] = [None]
    article[0] = types.InlineQueryResultArticle(
        id=result_id,
        title=title,
        description=description,
        input_message_content=types.InputTextMessageContent(
            message_text=title
        )
    )

    await inline_query.answer(
        article,
        cache_time=1,
        is_personal=True,
    )


@dp.inline_query()
async def currency(inline_query: types.InlineQuery) -> None:
    query = inline_query.query
    args = query.split()

    result_id = hashlib.md5(query.encode()).hexdigest()
    conv = CurrencyConverter()

    try:
        log.debug(len(args))
        if len(args) <= 1:
            await inline_reply(result_id,
                               "Требуется 2, либо 3 аргумента",
                               f"@shirino_bot USD RUB \n@shirino_bot 12 USD RUB", inline_query)

        if len(args) == 3:
            conv.amount = float(args[0])
            conv.from_currency = args[1].upper()
            conv.conv_currency = args[2].upper()
            conv.convert()
        elif len(args) == 2:
            conv.from_currency = args[0].upper()
            conv.conv_currency = args[1].upper()
            conv.convert()

        result = (
            f'{conv.amount} {conv.from_currency} = '
            f'{conv.conv_amount} {conv.conv_currency}'
        )

    except aiohttp.client_exceptions.ClientError as ex:
        await inline_reply(result_id,
                           "Rate-limit от API Telegram, повторите запрос позже",
                           None,
                           inline_query)

        log.debug(ex)
        await asyncio.sleep(1)

    except Exception as ex:
        log.debug(ex)
        await inline_reply(result_id, "Неверный формат данных",
                           "@shirino_bot USD RUB \n@shirino_bot 12 USD RUB",
                           inline_query)

    await inline_reply(result_id, result, None, inline_query)


async def main() -> None:
    bot = Bot(settings.telegram_token)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
