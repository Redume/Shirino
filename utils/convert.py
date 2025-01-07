import yaml
import requests

import json
import re

from datetime import datetime
from http import HTTPStatus

from decimal import Decimal, ROUND_DOWN
from utils.format_number import format_number

config = yaml.safe_load(open('config.yaml'))


class Converter:
    def __init__(self):
        self.amount: float = 1.0
        self.conv_amount: float = 0.0
        self.from_currency: str = ''
        self.conv_currency: str = ''


    def convert(self) -> None:
        if not self.kekkai() and not self.ddg():
            raise RuntimeError('Failed to convert via Kekkai or DDG')

        number = Decimal(str(self.conv_amount))
        self.conv_amount = format_number(number.quantize(Decimal('1.00'), rounding=ROUND_DOWN))


    def ddg(self) -> bool:
        try:
            res = requests.get(
                f'https://duckduckgo.com/js/spice/currency/'
                f'{self.amount}/{self.from_currency}/{self.conv_currency}',
                timeout=3
            )

            data = json.loads(re.findall(r'\(\s*(.*)\s*\);$', res.text)[0])

            for key in ['terms', 'privacy', 'timestamp']:
                data.pop(key, None)

            if not data.get('to'):
                return False

            self.conv_amount = float(data['to'][0].get('mid', 0.0))
            return True

        except (requests.exceptions.RequestException, json.JSONDecodeError, IndexError) as e:
            print(f"Error when requesting DDG: {e}")
            return False

    def kekkai(self) -> bool:
        date = datetime.today().strftime('%Y-%m-%d')
        try:
            res = requests.get(
                f"{config['kekkai_instance']}/api/getRate/",
                params={
                    'from_currency': self.from_currency,
                    'conv_currency': self.conv_currency,
                    'date': date,
                    'conv_amount': self.amount
                },
                timeout=3
            )

            if res.status_code != HTTPStatus.OK:
                return False

            data = res.json()
            self.conv_amount = data.get('conv_amount', 0.0)
            return True

        except (requests.exceptions.ConnectionError, json.JSONDecodeError) as e:
            print(f"Error when querying Kekkai: {e}")
            return False
