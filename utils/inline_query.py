import re

from aiogram import types


def esc_md(text: str) -> str:
    return re.sub(r"([_*\[\]()~`>#+\-=|{}.!\\])", r"\\\1", text)


async def reply(result_id: str, args: list, query: types.InlineQuery) -> None:
    if not args:
        return

    articles = []

    for idx, arg in enumerate(args):
        title = arg[0]
        description = arg[1] if arg[1] else None
        img = arg[2] if arg[2] else None

        if img:
            article = types.InlineQueryResultPhoto(
                id=f"{result_id}_{idx}",
                photo_url=img,
                thumbnail_url=img,
                title=title,
                description=description,
                caption=esc_md(title),
                parse_mode="MarkdownV2",
            )
        else:
            article = types.InlineQueryResultArticle(
                id=f"{result_id}_{idx}",
                title=title,
                description=description,
                input_message_content=types.InputTextMessageContent(
                    message_text=esc_md(title),
                    parse_mode="MarkdownV2",
                ),
            )

        articles.append(article)

    await query.answer(results=articles, cache_time=0, is_personal=True)
