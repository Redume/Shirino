# Shirino

## Что это?
Telegram-бот который выводит курс валюты используя DuckDuckGO и [CoinAPI](https://www.coinapi.io/).
https://t.me/Shirino_bot

## Хочу запустить
Получите токен бота в телеграме и токен CoinAPI.  
Вставьте в файл `.env` в формате:

```
COINAPI_KEY=Токен от апи CoinAPI
TELEGRAM_TOKEN=Токен Telegram-бота
```

В .env файл ещё можно такие переменные добавить:
```
DEBUG=false или true, включает отладочные логи
TIMEOUT=таймаут для библиотеки requests, в секундах (2 по дефолту)
```

## Хочу сделать пулл-реквест
Ставьте pylint и mypy для статической проверки кода.
Конфиги уже есть в репозитории.
После проверок можете открывать PR.
