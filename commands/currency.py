import hashlib

from aiogram import Command, types, Router

from main import bot
from functions.convert import Converter
from functions.create_chart import create_chart
from utils.format_number import format_number
from utils.inline_query import reply

router = Router()


@router.inline_query()
async def currency(query: types.InlineQuery) -> None:
    text = query.query.lower()
    args = text.split()
    result_id = hashlib.md5(text.encode()).hexdigest()

    get_bot = await bot.get_me()

    if len(args) < 2:
        return await reply(result_id,
                            [("2 or 3 arguments are required.",
                            f'@{get_bot.username} USD RUB \n'
                            f'@{get_bot.username} 12 USD RUB',
                            None, None)],
                            query)

    conv = Converter()

    from_currency, conv_currency = '', ''

    if len(args) == 3:
        try:
            conv.amount = float(args[0].replace(',', '.'))
            if conv.amount < 0:
                return await reply(
                    result_id,
                    [
                        ("Negative amounts are not supported.", None, None)
                        ],
                        query
                        )

        except ValueError:
            return await reply(
                result_id,
                [
                    (
                        "Please enter a valid number for the amount.",
                        f'@{get_bot.username} USD RUB \n'
                        f'@{get_bot.username} 12 USD RUB',
                        None, None
                    )
                ],
                query)

        from_currency = args[1]
        conv_currency = args[2]
    elif len(args) == 2:
        from_currency = args[0]
        conv_currency = args[1]
    else:
        return await reply(
            result_id,
            [
                (
                    'The source and target currency could not be determined.',
                    None, None
                )
            ],
            query
        )

    conv.from_currency = from_currency.upper()
    conv.conv_currency = conv_currency.upper()
    try:
        await conv.convert()
    except RuntimeError:
        return await reply(
            result_id,
            [
                (
                    'The currency exchange rate could not be determined', 
                    None, None
                )
            ],
            query
        )

    chart = await create_chart(from_currency, conv_currency)

    message = f'{format_number(conv.amount)} {conv.from_currency} ' \
    f'= {conv.conv_amount} {conv.conv_currency}'

    results = [(message, None, None)]

    if chart:
        results.insert(0, (f'{message}\n[Chart]({chart})', None, chart))

    await reply(result_id, results, query)