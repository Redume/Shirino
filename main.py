from functions.convert import Converter
from utils.format_number import format_number
from utils.inline_query import reply
from functions.create_chart import create_chart

import yaml

from aiohttp import web

from aiogram import Bot, Dispatcher, Router, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

import hashlib

config = yaml.safe_load(open('config.yaml'))
bot = Bot(token=config['telegram_token'], default=DefaultBotProperties(parse_mode=ParseMode.HTML))

router = Router()

@router.inline_query()
async def currency(query: types.InlineQuery) -> None:
    text = query.query.lower()
    args = text.split()
    result_id = hashlib.md5(text.encode()).hexdigest()

    if len(args) < 2:
            get_bot = await bot.get_me()
            return await reply(result_id, 
                                [("2 or 3 arguments are required.", 
                                f'@{get_bot.username} USD RUB \n'
                                f'@{get_bot.username} 12 USD RUB',
                                  None, None)],
                                query)

    conv = Converter()

    from_currency, conv_currency = '', ''

    if len(args) == 3:
        conv.amount = float(args[0].replace(',', '.'))
        from_currency = args[1]
        conv_currency = args[2]
    elif len(args) == 2:
        from_currency = args[0]
        conv_currency = args[1]
    else:
        return await reply(result_id,
                            [(
                                'The source and target currency could not be determined.',
                                None, None
                            )],
                            query)

    if not conv_currency or not from_currency:
        return await reply(result_id, [('The currency exchange rate could not be found.', None, None)], query)

    conv.from_currency = from_currency.upper()
    conv.conv_currency = conv_currency.upper()
    await conv.convert()

    chart = await create_chart(from_currency, conv_currency)

    message = f'{format_number(conv.amount)} {conv.from_currency} = {conv.conv_amount} {conv.conv_currency}'
    
    results = [(message, None, None)]
    
    if chart:
        results.insert(0, (f'{message}\n[График]({chart})', None, chart))
    
    await reply(result_id, results, query)


async def on_startup(bot: Bot) -> None:
    await bot.set_webhook(
        f"{config['webhook']['base_url']}{config['webhook']['path']}", 
        secret_token=config['webhook']['secret_token'],
        allowed_updates=['inline_query']
        )


def main() -> None:
    dp = Dispatcher()

    dp.include_router(router)
    dp.startup.register(on_startup)
    
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=config['webhook']['secret_token']
    )
    webhook_requests_handler.register(app, path=config['webhook']['path'])

    setup_application(app, dp, bot=bot)

    web.run_app(app, host='0.0.0.0', port=443)


if __name__ == '__main__':
    main()
