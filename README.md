# Shirino

> [!NOTE]
> Telegram-бот который выводит курс валюты используя DuckDuckGO и [Kekkai](https://github.com/Redume/Kekkai).
>
> https://t.me/shirino_bot

## Хочу запустить
<details>

Вставьте в файл `config.yaml` в формате:

```yaml
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
