from aiogram import Bot, Dispatcher, types

import yaml
import asyncio
import requests

import hashlib
import json

from http import HTTPStatus
import re

from function.convert import Converter
from function.format_number import format_number

dp = Dispatcher()
config = yaml.safe_load(open('config.yaml'))

@dp.inline_query()
async def currency(query: types.InlineQuery) -> None:
    global result, from_currency, conv_currency

    try:
        text = query.query.lower()
        args = text.split()
        result_id = hashlib.md5(text.encode()).hexdigest()

        conv = Converter()

        if len(args) < 2:
            return await reply(result_id, 
                                [("2 or 3 arguments are required.", 
                                '@shirino_bot USD RUB \n'
                                '@shirino_bot 12 USD RUB')], 
                                query)

        if len(args) == 3:
            conv.amount = float(args[0])
            from_currency = args[1]
            conv_currency = args[2]
        elif len(args) == 2:
            from_currency = args[0]
            conv_currency = args[1]
        else:
            return await reply(result_id, [('The source and target currency could not be determined.')], query)

        if not from_currency or not conv_currency:
            return await reply(result_id, [('The currency exchange rate could not be found.')], query)

        conv.from_currency = from_currency.upper()
        conv.conv_currency = conv_currency.upper()
        conv.convert()

        req_chart = requests.get(f'{config['kekkai_instance']}/api/getChart/week/', {
            'from_currency': from_currency,
            'conv_currency': conv_currency
        }, timeout=3)

        if not HTTPStatus(req_chart.status_code).is_success:
            req_chart = None
        else:
            req_chart = req_chart.json().get('message', None)

        await reply(result_id,
                    [
                        (
                            f'{format_number(conv.amount)} {conv.from_currency} = {conv.conv_amount} {conv.conv_currency}' \
                            f'\n{f'[График]({req_chart})' if req_chart else ''}',
                            None,
                            req_chart
                        ),
                        (
                            f'{format_number(conv.amount)} {conv.from_currency} = {conv.conv_amount} {conv.conv_currency}',
                            None,
                            None
                        )
                    ],
                    query)

    except Exception as e:
        print(e)


async def reply(result_id: str, args: list, query: types.InlineQuery) -> None:
    if not args:
        return

    articles = []

    for idx, arg in enumerate(args):
        title = arg[0]
        description = arg[1] if arg[1] else None
        img = arg[2] if arg[2] else None


        article = types.InlineQueryResultArticle(
            id=f"{result_id}_{idx}",
            title=remove_markdown(title).replace('График', ''),
            thumbnail_url=img, 
            description=description,
            input_message_content=types.InputTextMessageContent(
                message_text=title,
                parse_mode='markdown'
            )
        )

        articles.append(article)

    await query.answer(
        results=articles,
        parse_mode='markdown',
        cache_time=0,
        is_personal=True
    )

def remove_markdown(text: str) -> str:
    text = re.sub(r'\*([^\*]+)\*', r'\1', text)
    text = re.sub(r'\_([^\_]+)\_', r'\1', text)
    text = re.sub(r'\[([^\[]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'[`]+([^`]+)`+', r'\1', text)
    text = re.sub(r'~~([^~]+)~~', r'\1', text)
    text = re.sub(r'\[([^\[]+)\]\([^\)]+\)', '', text)
    return text


async def main() -> None:
    bot = Bot(config['telegram_token'])
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
