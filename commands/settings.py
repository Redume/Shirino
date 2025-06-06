import json
from typing import List, Optional, Tuple

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup)

from bot import db
from i18n.localization import I18n

router = Router()
i18n = I18n()

LangOption = Tuple[str, str]
PeriodOption = Tuple[str, str]

LANG_OPTIONS: List[LangOption] = [
    ("en", "English"),
    ("ru", "Русский"),
]

PERIOD_OPTIONS: List[PeriodOption] = [
    ("week", "week"),
    ("month", "month"),
    ("quarter", "quarter"),
    ("year", "year"),
]


async def get_user_locale(user_id: int) -> dict:
    data = await db.fetch("SELECT lang FROM users WHERE user_id = $1", user_id)
    if not data:
        await db.insert("INSERT INTO users (user_id) VALUES (?)", user_id)
        data = await db.fetch("SELECT lang FROM users WHERE user_id = $1", user_id)
    return i18n.get_locale(data.get("lang", "en"))


def build_options_keyboard(
    options: List[Tuple[str, str]],
    current_value: str,
    callback_prefix: str,
    locale: dict,
    buttons_per_row: int = 2,
    back_callback: Optional[str] = None,
) -> InlineKeyboardMarkup:
    buttons: List[List[InlineKeyboardButton]] = []
    row: List[InlineKeyboardButton] = []

    for code, label_key in options:
        label = locale.get(label_key, label_key)
        text = f"[X] {label}" if code == current_value else label
        row.append(
            InlineKeyboardButton(text=text, callback_data=f"{callback_prefix}_{code}")
        )
        if len(row) == buttons_per_row:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    if back_callback:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=locale["back"],
                    callback_data=back_callback,
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_chart_toggle_keyboard(
    chart_enabled: bool, locale: dict
) -> InlineKeyboardMarkup:
    toggle_text = locale["chart_disable"] if chart_enabled else locale["chart_enable"]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=toggle_text, callback_data="chart_toggle"),
                InlineKeyboardButton(
                    text=locale["chart_period"],
                    callback_data="chart_period",
                ),
                InlineKeyboardButton(
                    text=locale["setting_backend"],
                    callback_data="setting_backend",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=locale["back"],
                    callback_data="back_to_settings",
                ),
            ],
        ]
    )


def markup_to_json(
    markup: Optional[InlineKeyboardMarkup],
) -> Optional[str]:
    if markup is None:
        return None
    return json.dumps(markup.model_dump(), sort_keys=True)


async def safe_edit_message_text(
    callback: CallbackQuery,
    new_text: str,
    new_reply_markup: Optional[InlineKeyboardMarkup] = None,
    parse_mode: Optional[str] = None,
) -> None:
    message = callback.message
    current_text = (message.text or "").strip()
    new_text_clean = new_text.strip()

    is_text_same = current_text == new_text_clean
    is_markup_same = markup_to_json(message.reply_markup) == markup_to_json(
        new_reply_markup
    )

    if is_text_same and is_markup_same:
        await callback.answer()
        return

    await message.edit_text(
        new_text, reply_markup=new_reply_markup, parse_mode=parse_mode
    )
    await callback.answer()


@router.message(Command("settings"))
async def settings_handler(message: types.Message):
    locale = await get_user_locale(message.from_user.id)

    settings_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=locale["setting_chart"],
                    callback_data="setting_chart",
                ),
                InlineKeyboardButton(
                    text=locale["setting_lang"],
                    callback_data="setting_lang",
                ),
            ],
        ]
    )

    await message.answer(locale["settings_title"], reply_markup=settings_keyboard)


@router.callback_query(lambda c: c.data == "setting_lang")
async def show_language_menu(callback: CallbackQuery):
    locale = await get_user_locale(callback.from_user.id)

    data = await db.fetch(
        "SELECT lang FROM users WHERE user_id = $1", callback.from_user.id
    )
    current_lang = data.get("lang", "en")

    keyboard = build_options_keyboard(
        options=LANG_OPTIONS,
        current_value=current_lang,
        callback_prefix="lang",
        locale=locale,
        back_callback="back_to_settings",
    )

    await safe_edit_message_text(callback, locale["choose_language"], keyboard)


@router.callback_query(lambda c: c.data and c.data.startswith("lang_"))
async def language_selected(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    await db.update(
        "UPDATE users SET lang = $1 WHERE user_id = $2",
        lang,
        callback.from_user.id,
    )
    locale = i18n.get_locale(lang)

    keyboard = build_options_keyboard(
        options=LANG_OPTIONS,
        current_value=lang,
        callback_prefix="lang",
        locale=locale,
        back_callback="back_to_settings",
    )

    await safe_edit_message_text(callback, locale["choose_language"], keyboard)
    await callback.answer(locale["language_set"].format(lang=lang))


@router.callback_query(lambda c: c.data == "setting_backend")
async def show_backend_settings(callback: CallbackQuery):
    locale = await get_user_locale(callback.from_user.id)

    data = await db.fetch(
        "SELECT chart_backend, lang FROM users WHERE user_id = $1",
        callback.from_user.id,
    )
    current_backend = data["chart_backend"]
    backend_label = locale.get(current_backend, current_backend)

    keyboard = build_options_keyboard(
        options=[("typst", "Typst"), ("matplotlib", "Matplotlib")],
        current_value=current_backend,
        callback_prefix="backend",
        locale=locale,
        back_callback="back_to_settings",
    )

    await safe_edit_message_text(
        callback, f"{locale['choose_chart_backend']}", keyboard
    )


@router.callback_query(lambda c: c.data and c.data.startswith("backend_"))
async def set_backend(callback: CallbackQuery):
    backend = callback.data.split("_")[1]

    await db.update(
        "UPDATE users SET chart_backend = $1 WHERE user_id = $2",
        backend,
        callback.from_user.id,
    )

    locale = await get_user_locale(callback.from_user.id)

    keyboard = build_options_keyboard(
        options=[("typst", "Typst"), ("matplotlib", "Matplotlib")],
        current_value=backend,
        callback_prefix="backend",
        locale=locale,
        back_callback="back_to_settings",
    )

    await safe_edit_message_text(callback, locale["choose_chart_backend"], keyboard)


@router.callback_query(lambda c: c.data == "back_to_settings")
async def back_to_settings(callback: CallbackQuery):
    locale = await get_user_locale(callback.from_user.id)

    settings_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=locale["setting_chart"],
                    callback_data="setting_chart",
                ),
                InlineKeyboardButton(
                    text=locale["setting_lang"],
                    callback_data="setting_lang",
                ),
                InlineKeyboardButton(
                    text=locale["setting_backend"],
                    callback_data="setting_backend",
                ),
            ],
        ]
    )

    await safe_edit_message_text(
        callback, locale.get("settings_title", "Settings"), settings_keyboard
    )


@router.callback_query(lambda c: c.data == "setting_chart")
async def show_chart_settings(callback: CallbackQuery):
    data = await db.fetch(
        "SELECT * FROM users WHERE user_id = $1",
        callback.from_user.id,
    )
    lang = data.get("lang", "en")
    locale = i18n.get_locale(lang)

    chart_status = bool(data.get("chart", 1))
    period = data.get("chart_period")

    status_text = (
        locale.get("enabled", "Enabled")
        if chart_status
        else locale.get("disabled", "Disabled")
    )
    period_text = locale.get(period, period)

    text = (
        f"{locale['chart_settings']}\n"
        f"{locale['status']}: {status_text}\n"
        f"{locale['period']}: {period_text}\n"
        f"{locale['selected_chart_backend']}: {data.get('chart_backend')}"
    )
    keyboard = get_chart_toggle_keyboard(chart_status, locale)

    await safe_edit_message_text(callback, text, keyboard)


@router.callback_query(lambda c: c.data == "chart_toggle")
async def toggle_chart(callback: CallbackQuery):
    data = await db.fetch(
        "SELECT chart, lang FROM users WHERE user_id = $1", callback.from_user.id
    )
    lang = data.get("lang", "en")
    locale = i18n.get_locale(lang)

    current_status = data.get("chart", True)
    new_status = not current_status

    await db.update(
        "UPDATE users SET chart = $1 WHERE user_id = $2",
        new_status,
        callback.from_user.id,
    )

    await show_chart_settings(callback)


@router.callback_query(lambda c: c.data == "chart_period")
async def change_chart_period(callback: CallbackQuery):
    data = await db.fetch(
        "SELECT chart_period, lang FROM users WHERE user_id = $1", callback.from_user.id
    )
    lang = data.get("lang", "en")
    locale = i18n.get_locale(lang)

    current_period = data.get("chart_period")

    keyboard = build_options_keyboard(
        options=PERIOD_OPTIONS,
        current_value=current_period,
        callback_prefix="period",
        locale=locale,
        back_callback="setting_chart",
    )

    await safe_edit_message_text(callback, locale["choose_period"], keyboard)


@router.callback_query(lambda c: c.data and c.data.startswith("period_"))
async def set_chart_period(callback: CallbackQuery):
    period = callback.data.split("_")[1]
    await db.update(
        "UPDATE users SET chart_period = $1 WHERE user_id = $2",
        period,
        callback.from_user.id,
    )

    locale = await get_user_locale(callback.from_user.id)

    keyboard = build_options_keyboard(
        options=PERIOD_OPTIONS,
        current_value=period,
        callback_prefix="period",
        locale=locale,
        back_callback="setting_chart",
    )

    await safe_edit_message_text(callback, locale["choose_period"], keyboard)
