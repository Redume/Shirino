from aiogram import CommandStart, types, Router

from main import bot

router = Router()

@router.message(CommandStart())
async def start(message: types.Message) -> None:
    get_bot = await bot.get_me()
    await message.reply(
        'Shirino is a telegram bot for converting fiat or cryptocurrency. '
        'The example of use occurs via inline query:\n'
        f'`@{get_bot.username} USD RUB` \n'
        f'`@{get_bot.username} 12 USD RUB` \n\n'
        '[Source Code](https://github.com/Redume/Shirino)',
        parse_mode='markdown'
    )
