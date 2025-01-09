import yaml
import aiohttp

from http import HTTPStatus

config = yaml.safe_load(open('config.yaml'))

async def create_chart(from_currency: str, conv_currency: str) -> (dict, None):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
        async with session.get(f'{config["kekkai_instance"]}/api/getChart/month/', params={
            'from_currency': from_currency,
            'conv_currency': conv_currency
        }) as res:
            if not HTTPStatus(res.status).is_success:
                return None
            
            data = await res.json()

            return data.get('message', None)
