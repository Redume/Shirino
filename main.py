from aiogram import Bot, Dispatcher, types

import asyncio
import yaml
import hashlib
import aiohttp
import json

from function.convert import Converter

config = yaml.safe_load(open("config.yaml"))
dp = Dispatcher()


@dp.message()
async def message_conv(message: types.Message):
    query = message.text.split(' ')
    conv = Converter()

    amount = query[0]
    source_currency_alias = query[1]
    target_currency_alias = query[3]

    with open('currency.json', encoding='utf-8') as file:
        currency_json = json.loads(file.read())

    source_currency_code = None
    target_currency_code = None

    for currency_code, aliases in currency_json.items():
        if source_currency_alias in aliases:
            source_currency_code = currency_code

        elif target_currency_alias in aliases:
            target_currency_code = currency_code

        elif source_currency_code and target_currency_code:
            break
        else:
            return

    if source_currency_code and target_currency_code:
        conv.amount = float(amount)
        conv.from_currency = source_currency_code.upper()
        conv.conv_currency = target_currency_code.upper()
        conv.convert()

    result = (
        f'{conv.amount} {conv.from_currency} = '
        f'{conv.conv_amount} {conv.conv_currency}'
    )

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
