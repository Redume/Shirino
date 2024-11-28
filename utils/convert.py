import yaml
import requests

import json
import re

from decimal import Decimal, ROUND_DOWN
from utils.format_number import format_number

config = yaml.safe_load(open('config.yaml'))

coinapi_len = len(config['coinapi_keys'])
coinapi_active = [0]


class Converter:
    def __init__(self):
        self.amount: float = 1.0
        self.conv_amount: float = 0.0
        self.from_currency: str = ''
        self.conv_currency: str = ''

    def convert(self) -> None:
        if not self.ddg():
            self.coinapi()

        number = Decimal(str(self.conv_amount))

        self.conv_amount = format_number(number.quantize(Decimal('1.00'), rounding=ROUND_DOWN))

    def ddg(self) -> bool:
        res = requests.get('https://duckduckgo.com/js/spice/currency'
                           f'/{self.amount}'
                           f'/{self.from_currency}'
                           f'/{self.conv_currency}')

        data = json.loads(re.findall(r'\(\s*(.*)\s*\);$', res.text)[0])

        del data['terms']
        del data['privacy']
        del data['timestamp']

        if len(data.get('to')) == 0:
            return False

        conv = data.get('to')[0]
        conv_amount = conv.get('mid')

        if conv_amount is None:
            raise RuntimeError('Error when converting currency via DuckDuckGo')

        self.conv_amount = float(conv_amount)

        return True

    def coinapi(self, depth: int = config['coinapi_keys']) -> None:
        if depth <= 0:
            raise RecursionError('Rate limit on all tokens')

        resp = requests.get(
            (
                'https://rest.coinapi.io/v1/exchangerate'
                f'/{self.from_currency}'
                f'/{self.conv_currency}'
            ),
            headers={
                'X-CoinAPI-Key': config['coinapi_keys'][coinapi_active[0]],
            },
            timeout=config['timeout'],
        )

        if resp.status_code == 429:
            rotate_token(config['coinapi_keys'], coinapi_active)
            self.coinapi(depth - 1)

        data = resp.json()
        rate = data.get('rate')
        if rate is None:
            raise RuntimeError('Failed to get the exchange rate from CoinAPI')

        self.conv_amount = float(rate * self.amount)


def rotate_token(lst, active) -> None:
    active[0] = (active[0] + 1) % len(lst)
