### Telegram-bot

```
Телеграм-бот для отслеживания статуса проверки домашней работы на Яндекс.Практикум.
Присылает сообщения, когда статус проверки финального задания спринта изменен.
```

### Технологии:
- Python 3.9
- python-dotenv 0.19.0
- python-telegram-bot 13.7
- requests 2.26.0

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке.

Cоздать и активировать виртуальное окружение:

```
python -m venv env
```

```
. env/bin/activate
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Записать в переменные окружения (файл .env) необходимые ключи:
- токен профиля на Яндекс.Практикуме (PRACTICUM_TOKEN)
- токен телеграм-бота (TELEGRAM_TOKEN)
- id пользователя в телеграме для отправки уведомлений, бот должен быть активирован (TELEGRAM_CHAT_ID)


Запустить проект:

```
python homework.py
```
