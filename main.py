#!/usr/bin/env python3

import json
import hashlib

import logging
import string
from typing import Any, Dict, List, Optional

import requests

from pydantic import BaseSettings

from aiogram import Bot, types  # type: ignore
from aiogram.dispatcher import Dispatcher  # type: ignore
from aiogram.utils import executor  # type: ignore

from aiogram.types import InlineQuery  # type: ignore
from aiogram.types import InlineQueryResultArticle
from aiogram.types import InputTextMessageContent

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
bot = Bot(token=settings.telegram_token)
dp = Dispatcher(bot)


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
        """Get data from DuckDuckGo's currency API

        Returns:
            `False` if the currency does not exist,
            `True` on successful conversion
        """

        # API request
        resp = requests.get(
            (
                f'{DDG_URL}/{self.amount}/{self.from_currency}'
                f'/{self.conv_currency}'
            ),
            timeout=settings.timeout,
        )

        log.debug(resp.text)

        # Parsing JSON data
        data: Dict[str, Any] = json.loads(
            resp.text
            .replace('ddg_spice_currency(', '')
            .replace(');', '')
        )

        log.debug(data)

        # If the currency does not exist
        descr = data.get('headers', {}).get('description', '')
        if descr.find('ERROR') != -1:
            return False

        # Otherwise
        conv: Dict[str, str] = data.get('conversion', {})
        conv_amount = conv.get('converted-amount')
        if conv_amount is None:
            raise RuntimeError('Ошибка при конвертации через DDG')
        self.conv_amount = float(conv_amount)

        log.debug(conv)

        return True

    def coinapi(self, depth: int = coinapi_len) -> None:
        """Get data from CoinAPI (for cryptocurrencies)
        
        Args:
            depth (int, optional): Counter protecting from infinite recursion
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
    """Rotates API key to prevent ratelimits
    
    Args:
        lst (List[str]): Keys list
        active (List[str]): Mutable object with current key index
    """

    active[0] = (active[0] + 1) % len(lst)


@dp.inline_handler()
async def currency(inline_query: InlineQuery) -> None:
    query = inline_query.query
    article: List[Optional[InlineQueryResultArticle]] = [None]

    text = query.split()
    len_ = len(text)

    result_id = hashlib.md5(query.encode()).hexdigest()
    conv = CurrencyConverter()

    try:
        if len_ == 3:
            conv.amount = float(text[0])
            conv.from_currency = text[1].upper()
            conv.conv_currency = text[2].upper()
            conv.convert()
        elif len_ == 2:
            conv.from_currency = text[0].upper()
            conv.conv_currency = text[1].upper()
            conv.convert()
        else:
            raise ValueError('Надо 2 или 3 аргумента')

        result = (
            f'{conv.amount} {conv.from_currency} = '
            f'{conv.conv_amount} {conv.conv_currency}'
        )

    except Exception as ex:
        result = f'{type(ex).__name__}: {ex}'

    article[0] = InlineQueryResultArticle(
        id=result_id,
        title=result,
        input_message_content=InputTextMessageContent(
            message_text=result,
        ),
    )

    await inline_query.answer(
        article,  # type: ignore
        cache_time=1,
        is_personal=True,
    )


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Hi! Bot can show the exchange rate of crypto and fiat currency. "
                         "The bot is used through the inline commands "
                         "`@shirino_bot 12 usd rub` or `@shirino_bot usd rub`"
                         "\n\nThe bot is open source on [Github](https://github.com/redume/shirino)",
                         parse_mode="markdown")


executor.start_polling(dp, skip_updates=True)
