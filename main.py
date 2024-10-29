from aiogram import Bot, Dispatcher, types

import asyncio
import yaml

import hashlib

import json
from function.convert import Converter
from function.format_number import format_number

config = yaml.safe_load(open("config.yaml"))
dp = Dispatcher()


@dp.message()
@dp.inline_query()
async def currency(query: types.Message | types.InlineQuery) -> None:
    global result, from_currency, conv_currency

    try:
        text = query.query if isinstance(query, types.InlineQuery) else query.text
        args = text.split()
        result_id = hashlib.md5(text.encode()).hexdigest()
        conv = Converter()

        if len(args) <= 1:
            try:
                if query.chat.type in ['supergroup', 'group']:
                    return
            except:
                pass

            return await reply(result_id,
                            "2 or 3 arguments are required.",
                            "@shirino_bot USD RUB "
                            "\n@shirino_bot 12 USD RUB",
                            query)
        if len(args) == 4:
            conv.amount = float(args[0])
            from_currency = args[1].lower()
            conv_currency = args[3].lower()
        elif len(args) == 3:
            conv.amount = float(args[0])
            from_currency = args[1].lower()
            conv_currency = args[2].lower()
        elif len(args) == 2:
            from_currency = args[0].lower()
            conv_currency = args[1].lower()
        else:
            try:
                if query.chat.type in ['supergroup', 'group']:
                    return
            except:
                pass
            
            return await reply(result_id, 'The source and target currency could not be determined.', None, query)

        if not from_currency or not conv_currency:
            return await reply(result_id,
                               'The currency exchange rate could not be found.',
                               None,
                               query)

        conv.from_currency = from_currency.upper()
        conv.conv_currency = conv_currency.upper()
        conv.convert()

        result = f'{format_number(conv.amount)} {conv.from_currency} = {conv.conv_amount} {conv.conv_currency}'
        return await reply(result_id, result, None, query)

    except Exception as e:
        print(e)


async def reply(result_id: str | None, title: str | None, desc, query: types.InlineQuery | types.Message) -> None:
    if isinstance(query, types.InlineQuery):
        article = [None]
        article[0] = types.InlineQueryResultArticle(
            id=result_id,
            title=title,
            description=desc,
            input_message_content=types.InputTextMessageContent(
                message_text=title
            )
        )

        await query.answer(
            article,
            cache_time=1,
            is_personal=True,
        )
    else:
        await query.answer(f'{title} \n{desc}')


async def main() -> None:
    bot = Bot(config['telegram_token'])
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
