from http import HTTPStatus

import yaml
import requests
from urllib3 import HTTPSConnectionPool

config = yaml.safe_load(open('config.yaml'))

def get_chart(from_currency: str, conv_currency: str) -> (dict, None):
    try:
        res = requests.get(f'{config['kekkai_instance']}/api/getChart/week/', {
                    'from_currency': from_currency,
                    'conv_currency': conv_currency
                }, timeout=3)
    except requests.exceptions.ConnectionError:
        return None

    if not HTTPStatus(res.status_code).is_success:
        return None


    return res.json().get('message', None)