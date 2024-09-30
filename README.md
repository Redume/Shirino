# Shirino

> [!NOTE]
> Telegram-бот который выводит курс валюты используя DuckDuckGO и [CoinAPI](https://www.coinapi.io/).
>
> https://t.me/shirino_bot

## Хочу запустить
<details>

Получите токен бота в телеграме и токен CoinAPI.  
Вставьте в файл `config.yaml` в формате:

```yaml
coinapi_keys:
  - key1
  - key2
  - etc.
telegram_token: Токен Telegram-бота
```

В `config.yaml` файл ещё можно такие переменные добавить:
```yaml
debug: false # включает отладочные логи (false/true)
timeout: 2 # таймаут для библиотеки requests, в секундах (2 по дефолту)
```

</details>

## Хочу сделать Pull Request.
<details>
  Ставьте pylint и mypy для статической проверки кода.
  Конфиги уже есть в репозитории.
  После проверок можете открывать PR.
</details>

## Почему конфиг для CoinAPI - список?
<details>
  Можно получить несколько ключей на разные почтовые ящики
  и все ключи вписать в список:
  
  ```yaml
  coinapi_keys:
    - key1
    - key2
    - etc.
  ```

  Если вдруг один из них будет заблокирован по рейтлимиту,
  бот автоматически переключится на следующий (token rotation).
</details>