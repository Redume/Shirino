import yaml
import requests
from http import HTTPStatus

config = yaml.safe_load(open('config.yaml'))

def get_chart(from_currency: str, conv_currency: str) -> (dict, None):
    try:
        response = requests.get(f'{config["kekkai_instance"]}/api/getChart/week/', params={
            'from_currency': from_currency,
            'conv_currency': conv_currency
        }, timeout=3)
        
        if not HTTPStatus(response.status_code).is_success:
            return None

        try:
            data = response.json()
            return data.get('message', None)
        except ValueError:
            return None
    except requests.exceptions.ConnectionError:
        print("API connection error.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"There was an error: {e}")
        return None
