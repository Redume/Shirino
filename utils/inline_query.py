import re

from aiogram import types

async def reply(result_id: str, args: list, query: types.InlineQuery) -> None:
    if not args:
        return

    articles = []

    for idx, arg in enumerate(args):
        title = arg[0]
        description = arg[1] if arg[1] else None
        img = arg[2] if arg[2] else None


        article = types.InlineQueryResultArticle(
            id=f"{result_id}_{idx}",
            title=re.sub(
                r'\bChart\b|\[([^\]]+)\]\([^)]+\)',
                '',
                title,
                flags=re.IGNORECASE
            ),
            thumbnail_url=img,
            description=description,
            input_message_content=types.InputTextMessageContent(
                message_text=title,
                parse_mode='markdown'
            )
        )

        articles.append(article)

    await query.answer(
        results=articles,
        parse_mode='markdown',
        cache_time=0,
        is_personal=True
    )
