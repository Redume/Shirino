#!/usr/bin/env python3

import json
import hashlib

import logging
import string
from typing import Any, Dict, List, Optional

import requests

from pydantic import BaseSettings

from aiogram import Bot  # type: ignore
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
    coinapi_key: str
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

        # first non-zero +
        # 3 digits after zeroes or after the point
        # (settings.ndigit = 3 by default)
        after_point = after_point[:fnz + settings.ndigits]

        rounded = f'{str_amount[:point]}.{after_point}'
        self.conv_amount = float(rounded)

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

    def coinapi(self) -> None:
        """Get data from CoinAPI (for cryptocurrencies)"""

        resp = requests.get(
            (
                f'{COINAPI_URL}/{self.from_currency}'
                f'/{self.conv_currency}'
            ),
            headers={
                'X-CoinAPI-Key': settings.coinapi_key,
            },
            timeout=settings.timeout,
        )

        data: Dict[str, Any] = resp.json()
        rate = data.get('rate')
        if rate is None:
            raise RuntimeError('Не удалось получить курс валюты от CoinAPI')
        self.conv_amount = float(rate * self.amount)


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


executor.start_polling(dp, skip_updates=True)
