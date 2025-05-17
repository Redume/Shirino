from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, \
    InlineKeyboardButton, \
    CallbackQuery
import json

from bot import db
from i18n.localization import I18n

router = Router()
i18n = I18n()

lang_options = [
    ("en", "English"),
    ("ru", "Русский"),
]

period_options = [
    ("week", "week"),
    ("month", "month"),
    ("quarter", "quarter"),
    ("year", "year"),
]

def build_options_keyboard(
    options: list[tuple[str, str]],
    current_value: str,
    callback_prefix: str,
    locale: dict,
    buttons_per_row: int = 2,
    back_callback: str = None
) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for code, label_key in options:
        label = locale.get(label_key, label_key)
        text = f"[X] {label}" if code == current_value else label
        row.append(InlineKeyboardButton(
            text=text,
            callback_data=f"{callback_prefix}_{code}")
        )
        if len(row) == buttons_per_row:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    if back_callback:
        buttons.append([
            InlineKeyboardButton(
                text=locale.get("back"),
                callback_data=back_callback
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_chart_toggle_keyboard(
    chart_enabled: bool,
    locale: dict
) -> InlineKeyboardMarkup:
    toggle_text = locale.get("chart_disable") \
        if chart_enabled \
        else locale.get("chart_enable")

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=toggle_text,
                callback_data="chart_toggle"),
            InlineKeyboardButton(
                text=locale.get("chart_period"),
                callback_data="chart_period"
            ),
        ],
        [
            InlineKeyboardButton(
                text=locale.get("back"),
                callback_data="back_to_settings"
            ),
        ],
    ])

def markup_to_json(markup: InlineKeyboardMarkup | None) -> str | None:
    if markup is None:
        return None
    # model_dump() возвращает dict с данными
    return json.dumps(markup.model_dump(), sort_keys=True)

async def safe_edit_message_text(
    callback: CallbackQuery,
    new_text: str,
    new_reply_markup: InlineKeyboardMarkup | None = None,
    parse_mode: str | None = None,
) -> None:
    message = callback.message

    current_text = (message.text or "").strip()
    new_text_clean = new_text.strip()

    is_text_same = (current_text == new_text_clean)

    current_markup = message.reply_markup

    is_markup_same = markup_to_json(current_markup) == markup_to_json(new_reply_markup)

    if is_text_same and is_markup_same:
        await callback.answer()
        return

    await message.edit_text(
        new_text,
        reply_markup=new_reply_markup,
        parse_mode=parse_mode
    )
    await callback.answer()

@router.message(Command("settings"))
async def settings_handler(message: types.Message):
    data = await db.fetch(
        'SELECT lang FROM users WHERE user_id = $1',
        message.from_user.id
    )

    if not data:
        await db.insert(
            'INSERT INTO users (user_id) VALUES (?)',
            message.from_user.id
        )
        data = await db.fetch(
            'SELECT lang FROM users WHERE user_id = $1',
            message.from_user.id
        )

    lang = data.get('lang', 'en')
    locale = i18n.get_locale(lang)

    settings_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=locale.get("setting_chart"),
                callback_data="setting_chart"),
            InlineKeyboardButton(
                text=locale.get("setting_lang"),
                callback_data="setting_lang"),
        ],
    ])

    await message.answer(
        locale.get("settings_title"),
        reply_markup=settings_keyboard
    )

@router.callback_query(lambda c: c.data == "setting_lang")
async def show_language_menu(callback: CallbackQuery):
    data = await db.fetch(
        'SELECT lang FROM users WHERE user_id = $1',
        callback.from_user.id
    )
    lang = data.get('lang', 'en')
    locale = i18n.get_locale(lang)

    keyboard = build_options_keyboard(
        options=lang_options,
        current_value=lang,
        callback_prefix="lang",
        locale=locale,
        buttons_per_row=2,
        back_callback="back_to_settings"
    )
    await safe_edit_message_text(
        callback,
        new_text=locale.get("choose_language"),
        new_reply_markup=keyboard
    )

@router.callback_query(lambda c: c.data and c.data.startswith("lang_"))
async def language_selected(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    await db.update(
        'UPDATE users SET lang = $1 WHERE user_id = $2',
        lang, callback.from_user.id
    )
    locale = i18n.get_locale(lang)

    keyboard = build_options_keyboard(
        options=lang_options,
        current_value=lang,
        callback_prefix="lang",
        locale=locale,
        buttons_per_row=2,
        back_callback="back_to_settings"
    )

    await safe_edit_message_text(
        callback,
        new_text=locale.get("choose_language"),
        new_reply_markup=keyboard
    )

    await callback.answer(
        locale.get("language_set").format(lang=lang.upper())
    )

@router.callback_query(lambda c: c.data == "back_to_settings")
async def back_to_settings(callback: CallbackQuery):
    data = await db.fetch(
        'SELECT lang FROM users WHERE user_id = $1',
        callback.from_user.id
    )
    lang = data.get('lang', 'en')
    locale = i18n.get_locale(lang)

    settings_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=locale.get("setting_chart"),
                callback_data="setting_chart"),
            InlineKeyboardButton(
                text=locale.get("setting_lang"),
                callback_data="setting_lang"),
        ],
    ])

    await safe_edit_message_text(
        callback,
        new_text=locale.get("settings_title"),
        new_reply_markup=settings_keyboard
    )

@router.callback_query(lambda c: c.data == "setting_chart")
async def show_chart_settings(callback: CallbackQuery):
    data = await db.fetch(
        'SELECT chart, chart_period, lang FROM users WHERE user_id = $1',
        callback.from_user.id
    )
    lang = data.get('lang', 'en')
    locale = i18n.get_locale(lang)

    chart_status = bool(data.get('chart', 1))
    period = data.get('chart_period')

    status_text = locale.get("enabled", "Enabled") \
        if chart_status \
        else locale.get("disabled", "Disabled")

    period_text = locale.get(period, period)

    text = (
        f"{locale.get('chart_settings')}\n"
        f"{locale.get('status')}: {status_text}\n"
        f"{locale.get('period')}: {period_text}"
    )

    keyboard = get_chart_toggle_keyboard(chart_status, locale)

    await safe_edit_message_text(
        callback,
        new_text=text,
        new_reply_markup=keyboard
    )

@router.callback_query(lambda c: c.data == "chart_toggle")
async def toggle_chart(callback: CallbackQuery):
    data = await db.fetch(
        'SELECT chart, lang FROM users WHERE user_id = $1',
        callback.from_user.id
    )
    lang = data.get('lang', 'en')
    locale = i18n.get_locale(lang)

    current_status = data.get('chart', True)
    new_status = not current_status

    await db.update(
        'UPDATE users SET chart = $1 WHERE user_id = $2',
        new_status, callback.from_user.id
    )

    await callback.answer(
        locale.get(f"chart_now_{'enabled' if new_status else 'disabled'}",
                   f"Chart now {'enabled' if new_status else 'disabled'}")
    )

    await show_chart_settings(callback)

@router.callback_query(lambda c: c.data == "chart_period")
async def change_chart_period(callback: CallbackQuery):
    data = await db.fetch(
        'SELECT chart_period, lang FROM users WHERE user_id = $1',
        callback.from_user.id
    )
    lang = data.get('lang', 'en')
    locale = i18n.get_locale(lang)

    current_period = data.get('chart_period')

    keyboard = build_options_keyboard(
        options=period_options,
        current_value=current_period,
        callback_prefix="period",
        locale=locale,
        buttons_per_row=2,
        back_callback="setting_chart"
    )
    await safe_edit_message_text(
        callback,
        new_text=locale.get("choose_period"),
        new_reply_markup=keyboard
    )

@router.callback_query(lambda c: c.data and c.data.startswith("period_"))
async def set_chart_period(callback: CallbackQuery):
    period = callback.data.split("_")[1]
    await db.update(
        'UPDATE users SET chart_period = $1 WHERE user_id = $2',
        period, callback.from_user.id
    )
    data = await db.fetch(
        'SELECT lang FROM users WHERE user_id = $1',
        callback.from_user.id
    )
    lang = data.get('lang', 'en')
    locale = i18n.get_locale(lang)

    keyboard = build_options_keyboard(
        options=period_options,
        current_value=period,
        callback_prefix="period",
        locale=locale,
        buttons_per_row=2,
        back_callback="setting_chart"
    )

    await safe_edit_message_text(
        callback,
        new_text=locale.get("choose_period"),
        new_reply_markup=keyboard
    )

    await callback.answer(
        locale.get("period_set").format(period=period)
    )
