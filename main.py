import logging
import sys

import yaml

from aiohttp import web

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

config = yaml.safe_load(open('config.yaml'))

router = Router()

@router.message()
async def echo_handler(message: Message) -> None:
    try:
        # Send a copy of the received message
        await message.send_copy(chat_id=message.chat.id)
    except TypeError:
        # But not all the types is supported to be copied so need to handle it
        await message.answer("Nice try!")

async def on_startup(bot: Bot) -> None:
    # Убедитесь, что передаете HTTPS URL
    await bot.set_webhook(f"{config['webhook']['base_url']}{config['webhook']['path']}", secret_token=config['webhook']['secret_token'])


def main() -> None:
    dp = Dispatcher()

    dp.include_router(router)
    dp.startup.register(on_startup)
    
    bot = Bot(token=config['telegram_token'], default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=config['webhook']['secret_token']
    )
    webhook_requests_handler.register(app, path=config['webhook']['path'])

    setup_application(app, dp, bot=bot)

    web.run_app(app, host='127.0.0.1', port=8080)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main()
