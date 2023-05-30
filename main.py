import requests
import json
import hashlib

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor


bot = Bot(token="5193950006:AAGU8elNfNB9FocVSIb4DnqoEvQk70Mqh5E")
dp = Dispatcher(bot)


class TypeDict:
    def __init__(self):
        self.amount = None
        self.from_amount = None
        self.from_currency = None
        self.to_currency = None

    @staticmethod
    def get_currency(self, amount, from_currency, to_currency):
        if amount is None:
            amount = "1"

        try:
            page = requests.get(f"https://duckduckgo.com/js/spice/currency/{amount}/{from_currency}/{to_currency}")
            page = page.text.replace('ddg_spice_currency(', "").replace(');', "")
            page = json.loads(page)

            if page["headers"]["description"].find("ERROR") != -1:
                print(from_currency, to_currency)
                crypto = requests.get(f"https://rest.coinapi.io/v1/exchangerate/{from_currency.upper()}/{to_currency.upper()}", headers={
                    "X-CoinAPI-Key": "8A465920-C233-4EE2-860B-A0AF9EC21FFF"
                }).json()

                print(crypto)

                self.from_amount = crypto.get("rate")
                return crypto.get("rate")

        except KeyError:
            print("blyat slomal")
            return None

        return page.get("conversion")

    @staticmethod
    def is_num(value):
        return value.isdecimal() or value.replace('.', '', 1).isdecimal()


type_dict = TypeDict()


@dp.inline_handler()
async def currency(query: types.InlineQuery):
    text = query.query.split(" ")
    result_id: str = hashlib.md5(query.query.encode()).hexdigest()

    if text == ['']:
        return

    for i in range(len(text)):
        if type_dict.is_num(text[i]):
            continue

        if text[i].find(",") != -1:
            text[i] = text[i].replace(",", ".")

    try:
        if type_dict.is_num(text[0]):
            res, crypto_rate = type_dict.get_currency(text[0], text[1], text[2])
        else:
            res, crypto_rate = type_dict.get_currency(None, text[0], text[1])
    except Exception:
        return

    if res is None:
        return

    print(res)

    from_amount = res.get('from_amount', res['from-amount'])
    from_currency_symbol = res.get('from_currency_symbol', res['from-currency-symbol'])
    converted_amount = res.get('converted_amount', res['converted-amount'])
    to_currency_symbol = res.get('to_currency_symbol', res['to-currency-symbol'])

    result = f"{from_amount} {from_currency_symbol} = {converted_amount} {to_currency_symbol}"

    if crypto_rate:
        result += f" | Crypto Rate: {crypto_rate}"

    article = [types.InlineQueryResultArticle(
        id=result_id,
        title=result,
        input_message_content=types.InputTextMessageContent(
            message_text=result
        ))]

    await query.answer(article, cache_time=1, is_personal=True)

executor.start_polling(dp, skip_updates=True)
