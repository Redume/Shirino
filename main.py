from aiogram import Bot, Dispatcher, types

import asyncio
import yaml

import hashlib
import aiohttp

import json
import re

from word2number import w2n
from function.convert import Converter

config = yaml.safe_load(open("config.yaml"))
dp = Dispatcher()


@dp.message()
async def message_conv(message: types.Message):
    with open('currency.json', 'r', encoding='utf-8') as f:
        currency_json = json.load(f)

    text = message.text.lower()
    args = text.split()

    number_match = re.match(r'\d+\.?\d*|\w+', args[0])
    if number_match:
        number_text = number_match.group(0)

        try:
            amount = float(number_text)
        except ValueError:
            try:
                amount = float(w2n.word_to_num(number_text))
            except ValueError:
                await message.reply("Не удалось распознать числовое значение.")
                return
    else:
        await message.reply("Не удалось найти числовое значение.")
        return

    if len(args) == 4:
        source_currency_alias = args[1]
        target_currency_alias = args[3]
    elif len(args) == 3:
        source_currency_alias = args[0]
        target_currency_alias = args[2]
    else:
        await message.reply("Не удалось определить исходную и целевую валюту.")
        return

    source_currency_code = None
    target_currency_code = None

    for currency_code, aliases in currency_json.items():
        if source_currency_alias in aliases:
            source_currency_code = currency_code
        if target_currency_alias in aliases:
            target_currency_code = currency_code

    if not source_currency_code or not target_currency_code or amount is None:
        await message.reply("Не удалось найти сумму или валюты по указанным данным.")
        return

    conv = Converter()
    conv.amount = amount
    conv.from_currency = source_currency_code.upper()
    conv.conv_currency = target_currency_code.upper()
    conv.convert()

    result = f'{conv.amount} {conv.from_currency} = {conv.conv_amount} {conv.conv_currency}'
    await message.reply(result)


async def inline_reply(result_id: str, title: str, description: str or None, inline_query: types.InlineQuery) -> None:
    article = [None]
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
    global result
    query = inline_query.query
    args = query.split()

    result_id = hashlib.md5(query.encode()).hexdigest()
    conv = Converter()

    try:
        if len(args) <= 1:
            await inline_reply(result_id,
                               "2 or 3 arguments are required",
                               f"@shirino_bot USD RUB \n@shirino_bot 12 USD RUB", inline_query)

        if len(args) == 3:
            conv.amount = float(args[0].replace(',', '.'))
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

    except aiohttp.client_exceptions.ClientError:
        await inline_reply(result_id,
                           "Rate-limit from the Telegram API, repeat the request later",
                           None,
                           inline_query)

        await asyncio.sleep(1)

    except Exception:
        await inline_reply(result_id, "Invalid data format",
                           "@shirino_bot USD RUB \n@shirino_bot 12 USD RUB",
                           inline_query)

    await inline_reply(result_id, result, None, inline_query)


async def main() -> None:
    bot = Bot(config['telegram_token'])
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
