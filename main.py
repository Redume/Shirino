#!/usr/bin/env python3
import aiohttp.client_exceptions
from pydantic.v1 import BaseSettings
from typing import List, Any, Dict, Optional
import logging

from aiogram import Dispatcher, types, Bot

import requests
import json

import hashlib

import asyncio

import re
import string


class Settings(BaseSettings):
    debug: bool
    coinapi_keys: List[str]
    telegram_token: str

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()

log = logging.getLogger('shirino')
handler = logging.StreamHandler()
fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

handler.setFormatter(fmt)
log.addHandler(handler)

if settings.debug:
    handler.setLevel(logging.DEBUG)
    log.setLevel(logging.DEBUG)

coinapi_len = len(settings.coinapi_keys)
coinapi_active = [0]

dp = Dispatcher()

DDG_URL = 'https://duckduckgo.com/js/spice/currency'
COINAPI_URL = 'https://rest.coinapi.io/v1/exchangerate'


class Currency:
    def __init__(self) -> None:
        self.amount: float = 1.0
        self.conv_amount: float = 1.0
        self.from_currency = ''
        self.conv_currency = ''

    def convert(self) -> None:
        if not self.ddg():
            self.coinapi()

        str_amount = f'{self.conv_amount}'
        point = str_amount.find('.')
        after_point = str_amount[point + 1:]

        fnz = min(
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
        ndigits = fnz + 3

        self.conv_amount = round(self.conv_amount, ndigits)

    def ddg(self) -> float:
        """Получение данных фиатной валюты через DuckDuckGo

        e.g: https://duckduckgo.com/js/spice/currency/1/USD/RUB
        """

        res = requests.get(f'{DDG_URL}/{self.amount}/{self.from_currency}/{self.conv_currency}')
        data: Dict[str, Any] = json.loads(re.findall(r'(.+)\);', res.text)[0])

        log.debug(data)

        if len(data.get('to')) == 0:
            return False

        conv: Dict[str, str] = data.get('to')[0]
        conv_amount = conv.get("mid")

        if conv_amount is None:
            print("FUCK")
            raise RuntimeError('Ошибка при конвертации валюты через DuckDuckGo')

        log.debug(conv)
        log.debug(conv_amount)

        self.conv_amount = float(conv_amount)

        return True

    def coinapi(self, depth: int = coinapi_len) -> None:
        """Получение данных с CoinAPI для получения курса криптовалюты

        Args:
            depth (int, optional): Счетчик, защищающий от бесконечной рекурсии
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
            timeout=3,
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


@dp.inline_query()
async def currency(inline_query: types.InlineQuery) -> None:
    query = inline_query.query
    article: List[Optional[types.InlineQueryResultArticle]] = [None]

    args = query.split()

    result_id = hashlib.md5(query.encode()).hexdigest()
    conv = Currency()

    try:
        if len(args) == 0:
            article[0] = types.InlineQueryResultArticle(
                id=result_id,
                title="Требуется 2, либо 3 аргумента",
                description=f"@shirino_bot USD RUB \n@shirino_bot 12 USD RUB",
                input_message_content=types.InputTextMessageContent(
                    message_text="Требуется 2, либо 3 аргумента"
                )
            )

        elif args[0].isdigit() or re.match(r'^-?\d+(?:\.\d+)$', args[0]) is not None:
            conv.from_currency = args[1].upper()
            conv.conv_currency = args[2].upper()
            conv.convert()
        elif type(args[0]) is str:
            conv.from_currency = args[0].upper()
            conv.conv_currency = args[1].upper()
            conv.convert()

        result_title = f'{conv.amount} {conv.from_currency} = {conv.conv_amount} {conv.conv_currency}'
        result_desc = None


    except aiohttp.client_exceptions.ClientError:
        result_title = 'Произошла ошибка'
        result_desc = 'Рейт-лимит от api telegram, попробуйте позже'
        await asyncio.sleep(1)

    except Exception as ex:
        log.debug(ex)
        result_title = 'Произошла ошибка'
        result_desc = f'{type(ex).__name__}: {ex}'

    article[0] = types.InlineQueryResultArticle(
        id=result_id,
        title=result_title,
        description=result_desc,
        input_message_content=types.InputTextMessageContent(
            message_text=f"{result_title} \n{result_desc}",
        ),
    )

    await inline_query.answer(
        article,
        cache_time=1,
        is_personal=True,
    )


async def main() -> None:
    bot = Bot(settings.telegram_token)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
