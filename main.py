import yaml

from aiohttp import web

from aiogram import Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from commands import currency, start, settings
from database.server import Database
from bot import bot

config = yaml.safe_load(open('../config.yaml', 'r', encoding='utf-8'))
db = Database('shirino.db')

async def on_startup(bot: bot) -> None:
    await db.connect()
    await db._create_table()
    await bot.set_webhook(
        f"{config['webhook']['base_url']}{config['webhook']['path']}",
        secret_token=config['webhook']['secret_token'],
        allowed_updates=['inline_query', 'message']
        )


async def on_shutdown():
    await db.disconnect()


def main() -> None:
    dp = Dispatcher()

    dp.include_router(currency.router)
    dp.include_router(start.router)
    dp.include_router(settings.router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

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
