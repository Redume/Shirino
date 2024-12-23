import yaml
import requests

import json
import re

from datetime import datetime
from http import HTTPStatus

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
        if not self.kekkai():
            self.ddg()

        number = Decimal(str(self.conv_amount))

        self.conv_amount = format_number(number.quantize(Decimal('1.00'), rounding=ROUND_DOWN))

    def ddg(self) -> None:
        res = requests.get('https://duckduckgo.com/js/spice/currency'
                           f'/{self.amount}'
                           f'/{self.from_currency}'
                           f'/{self.conv_currency}')

        data = json.loads(re.findall(r'\(\s*(.*)\s*\);$', res.text)[0])

        del data['terms']
        del data['privacy']
        del data['timestamp']

        if len(data.get('to')) == 0:
            raise RuntimeError('Failed to get the exchange rate from DDG')

        conv = data.get('to')[0]
        conv_amount = conv.get('mid')

        if conv_amount is None:
            raise RuntimeError('Error when converting currency via DuckDuckGo')

        self.conv_amount = float(conv_amount)


    def kekkai(self) -> bool:
        date = datetime.today().strftime('%Y-%m-%d')

        try:
            res = requests.get(f'{config['kekkai_instance']}/api/getRate/', {
                'from_currency': self.from_currency,
                'conv_currency': self.conv_currency,
                'date': date,
                'conv_amount': self.amount
            }, timeout=3)

            data = res.json()

            if not HTTPStatus(res.status_code).is_success:
                return False


            self.conv_amount = data.get('conv_amount')

            return True
        except requests.exceptions.ConnectionError:
            return False


