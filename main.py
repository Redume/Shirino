from aiogram import Bot, Dispatcher, types

import yaml
import asyncio

import hashlib

from function.get_chart import get_chart
from utils.convert import Converter
from utils.format_number import format_number
from function.inline_query import reply

dp = Dispatcher()
config = yaml.safe_load(open('config.yaml'))

@dp.inline_query()
async def currency(query: types.InlineQuery) -> None:
    global from_currency, conv_currency

    try:
        text = query.query.lower()
        args = text.split()
        result_id = hashlib.md5(text.encode()).hexdigest()

        conv = Converter()

        if len(args) < 2:
            return await reply(result_id, 
                                [("2 or 3 arguments are required.", 
                                '@shirino_bot USD RUB \n'
                                '@shirino_bot 12 USD RUB',
                                  None, None)],
                                query)

        if len(args) == 3:
            conv.amount = float(args[0].replace(',', '.'))
            from_currency = args[1]
            conv_currency = args[2]
        elif len(args) == 2:
            from_currency = args[0]
            conv_currency = args[1]
        else:
            return await reply(result_id,
                               [
                                   (
                                       'The source and target currency could not be determined.',
                                       None,
                                       None
                                   )
                               ],
                               query)

        if not from_currency or not conv_currency:
            return await reply(result_id, [('The currency exchange rate could not be found.', None, None)], query)

        conv.from_currency = from_currency.upper()
        conv.conv_currency = conv_currency.upper()
        conv.convert()

        chart = get_chart(from_currency, conv_currency)

        if not chart:
            return await reply(result_id,
                               [
                                   (
                                       f'{format_number(conv.amount)} {conv.from_currency} '
                                       f'= {conv.conv_amount} {conv.conv_currency}' \
                                       f'\n{f'[График]({chart})' if chart else ''}',
                                       None,
                                       chart
                                   )
                               ],
                               query)

        await reply(result_id,
                    [
                        (
                            f'{format_number(conv.amount)} {conv.from_currency} '
                            f'= {conv.conv_amount} {conv.conv_currency}' \
                            f'\n{f'[График]({chart})' if chart else ''}',
                            None,
                            chart
                        ),
                        (
                            f'{format_number(conv.amount)} {conv.from_currency} '
                            f'= {conv.conv_amount} {conv.conv_currency}',
                            None,
                            None
                        )
                    ],
                    query)

    except Exception as e:
        print(e)



async def main() -> None:
    bot = Bot(config['telegram_token'])
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
