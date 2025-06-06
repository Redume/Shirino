from http import HTTPStatus
from urllib.parse import urlencode

import yaml
import aiohttp

config = yaml.safe_load(open('../config.yaml', 'r', encoding='utf-8'))

async def create_chart(
    from_currency: str,
    conv_currency: str,
    period: str,
    backend: str) -> (str, None):
    params = {
        'from_currency': from_currency,
        'conv_currency': conv_currency,
        'period': period,
        'backend': backend
    }
    
    base_url = f'{config["kekkai_instance"]}/api/getChart/'
    query_string = urlencode(params)
    full_url = f'{base_url}?{query_string}'

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
        async with session.get(full_url) as res:
            if not HTTPStatus(res.status).is_success:
                return None
    
            return full_url
