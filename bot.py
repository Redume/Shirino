from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import yaml

from database.server import Database

db = Database('/data/shirino.db')
config = yaml.safe_load(open('../config.yaml', 'r', encoding='utf-8'))
bot = Bot(
    token=config['telegram_token'],
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )