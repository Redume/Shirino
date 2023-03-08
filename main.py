import requests
import json
import hashlib

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor


bot = Bot(token="")
dp = Dispatcher(bot)


def get_currency(amount, from_currency, to_currency):
    if amount is None:
        amount = "1"

    try:
        page = requests.get(f"https://duckduckgo.com/js/spice/currency/{amount}/{from_currency}/{to_currency}")
        page = page.text.replace('ddg_spice_currency(', "").replace(');', "")
        page = json.loads(page)
        if page["headers"]["description"].find("ERROR") != -1:
            return

    except KeyError:
        return print("Чет сломалось")

    return page["conversion"]


def isNum(value):
    return value.isdecimal() or value.replace('.', '', 1).isdecimal()


@dp.inline_handler()
async def currency(query: types.InlineQuery):
    text = query.query.split(" ")
    result_id: str = hashlib.md5(query.query.encode()).hexdigest()

    if text == ['']:
        return

    for i in range(len(text)):
        if isNum(text[0]):
            continue

        if text[i].find(",") != -1:
            text[i] = text[i].replace(",", ".")

    result: str
    try:
        if isNum(text[0]):
            res = get_currency(text[0], text[1], text[2])
        else:
            res = get_currency(None, text[0], text[1])
    except Exception:
        return

    result = f"{res['from-amount']} {res['from-currency-symbol']} = {res['converted-amount']} {res['to-currency-symbol']}"

    article = [types.InlineQueryResultArticle(
        id=result_id,
        title="The rate of a certain currency",
        input_message_content=types.InputTextMessageContent(
            message_text=str(result)
        ))]

    await query.answer(article, cache_time=1, is_personal=True)


executor.start_polling(dp, skip_updates=True)
