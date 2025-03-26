import json
import re
from datetime import datetime
from decimal import Decimal
from http import HTTPStatus

import aiohttp
import yaml

from utils.format_number import format_number

config = yaml.safe_load(open('config.yaml', 'r', encoding='utf-8'))

class Converter:
    def __init__(self):
        self.amount: float = 1.0
        self.conv_amount: float = 0.0
        self.from_currency: str = ''
        self.conv_currency: str = ''

    async def convert(self) -> None:
        if not await self.kekkai():
            await self.ddg()

        self.conv_amount = format_number(Decimal(self.conv_amount))


    async def kekkai(self) -> bool:
        date = datetime.today().strftime('%Y-%m-%d')

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
            async with session.get(f'{config['kekkai_instance']}/api/getRate/', params={
                'from_currency': self.from_currency,
                'conv_currency': self.conv_currency,
                'date': date,
                'conv_amount': self.amount
            }) as res:
                if not HTTPStatus(res.status).is_success:
                    return False

                data = await res.json()
                self.conv_amount = data.get('conv_amount', 0.0)

                return True


    async def ddg(self) -> None:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=3)
            ) as session:
            async with session.get(
                'https://duckduckgo.com/js/spice/currency/'
                f'{self.amount}/{self.from_currency}/{self.conv_currency}'
                ) as res:

                data_text = await res.text()

                data = json.loads(re.findall(r'\(\s*(.*)\s*\);$', data_text)[0])

                for key in ['terms', 'privacy', 'timestamp']:
                    data.pop(key, None)

                if not data.get('to'):
                    raise RuntimeError(
                        'Failed to get the exchange rate from DuckDuckGo'
                        )

                conv = data.get('to')[0]
                conv_amount = conv.get('mid')

                if conv_amount is None:
                    raise RuntimeError(
                        'Error when converting currency via DuckDuckGo'
                        )

                self.conv_amount = float(conv_amount)
