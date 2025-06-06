import hashlib

from aiogram import types, Router
from aiogram.filters import Command

from bot import bot, db
from functions.convert import Converter
from functions.create_chart import create_chart
from utils.format_number import format_number
from utils.inline_query import reply
from i18n.localization import I18n

router = Router()
i18n = I18n()


@router.inline_query()
async def currency(query: types.InlineQuery) -> None:
    text = query.query.lower()
    args = text.split()
    result_id = hashlib.md5(text.encode()).hexdigest()
    get_bot = await bot.get_me()

    data = await db.fetch(
        'SELECT * FROM users WHERE user_id = ?', 
        query.from_user.id
    )

    lang = data.get('lang')
    locale = i18n.get_locale(lang)

    currency_example = locale["currency_example"].format(
        bot_username=get_bot.username
        )

    if len(args) < 2:
        await reply(
            result_id,
            [(locale["error_not_enough_args"], currency_example, None, None)],
            query
        )
        return

    conv = Converter()

    from_currency, conv_currency = '', ''

    if len(args) == 3:
        try:
            conv.amount = float(args[0].replace(',', '.'))
            if conv.amount < 0:
                await reply(
                    result_id,
                    [(locale["error_negative_amount"], None, None)],
                    query
                )
                return
        except ValueError:
            await reply(
                result_id,
                [(locale["error_invalid_number"], currency_example, None, None)],
                query
            )
            return
        from_currency = args[1]
        conv_currency = args[2]
    elif len(args) == 2:
        from_currency = args[0]
        conv_currency = args[1]
    else:
        await reply(
            result_id,
            [(locale["error_unknown_currency"], None, None)],
            query,
        )
        return

    conv.from_currency = from_currency.upper()
    conv.conv_currency = conv_currency.upper()

    try:
        await conv.convert()
    except RuntimeError:
        await reply(
            result_id,
            [(locale["error_currency_rate"], None, None)],
            query
        )
        return

    chart = None

    if bool(data.get('chart', 1)):
        chart = await create_chart(
            from_currency,
            conv_currency,
            data.get('chart_period', 'month'),
            data.get('chart_backend', 'matplotlib')
        )

    message = (
        f"{format_number(conv.amount)} {conv.from_currency} = "
        f"{conv.conv_amount} {conv.conv_currency}"
    )
    results = [(message, None, None)]

    if chart:
        results.insert(
            0, 
            (
                message, 
                None, 
                chart
            )
        )

    await reply(result_id, results, query)
