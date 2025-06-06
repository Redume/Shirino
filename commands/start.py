import re

from aiogram import Router, types
from aiogram.filters import CommandStart

from bot import bot, db
from i18n.localization import I18n

router = Router()
i18n = I18n()


def escape_md_v2(text: str) -> str:
    return re.sub(r"([_*\[\]()~#+\-=|{}.!\\])", r"\\\1", text)


@router.message(CommandStart())
async def start(message: types.Message) -> None:
    get_bot = await bot.get_me()

    data = await db.fetch(
        "SELECT lang FROM users WHERE user_id = $1", message.from_user.id
    )

    locale = i18n.get_locale(data.get("lang"))

    raw_template = locale.get("start_message")
    raw_text = raw_template.format(bot_username=get_bot.username)
    text = escape_md_v2(raw_text)

    button_text = locale.get("source_code_button")

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=button_text, url="https://github.com/redume/shirino"
                )
            ]
        ]
    )

    await message.reply(text, parse_mode="MarkdownV2", reply_markup=keyboard)
