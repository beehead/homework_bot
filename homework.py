"""Бот для проверки статуса домашних заданий."""
import logging
import os
import sys
import time

import requests
import telegram

import exceptions

from dotenv import load_dotenv

load_dotenv()

LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка наличия данных в .env"""
    return None not in (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)


def send_message(bot, message):
    """отправляет сообщение в Telegram чат,
    определяемый переменной окружения TELEGRAM_CHAT_ID.
    Принимает на вход два параметра: экземпляр класса Bot
    и строку с текстом сообщения."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logging.debug('Сообщение отправлено в tg')
    except RuntimeError:
        logging.error('Ошибка отправки в tg')


def get_api_answer(timestamp):
    """делает запрос к единственному эндпоинту API-сервиса.
    В качестве параметра в функцию передается временная метка.
    В случае успешного запроса должна вернуть ответ API,
    приведя его из формата JSON к типам данных Python."""
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    payload = {'from_date': timestamp}
    try:
        response = requests.get(
            ENDPOINT,
            headers=headers,
            params=payload
        )
    except requests.exceptions.Timeout:
        logging.error('API timeout')
    except requests.exceptions.ConnectionError:
        logging.error('API connection error')
    except requests.exceptions.HTTPError:
        logging.error('API status not 200')
    return response.json()


def check_response(response):
    """проверяет ответ API на соответствие документации.
    В качестве параметра функция получает ответ API,
    приведенный к типам данных Python."""
    if isinstance(response['homeworks'], dict):
        logging.error('Ответ не является словарём')
        raise TypeError('Ответ не является словарём')
    homeworks_list = response['homeworks']
    if homeworks_list == []:
        logging.debug('Новые статусы отсутствуют')
        return None
    logging.debug('Ответ получен, трубуется анализ')
    return homeworks_list


def parse_status(homework):
    """извлекает из информации о конкретной домашней работе
    статус этой работы. В качестве параметра функция получает
    только один элемент из списка домашних работ.
    В случае успеха, функция возвращает подготовленную для отправки
    в Telegram строку, содержащую один из вердиктов словаря
    HOMEWORK_VERDICTS."""
    homework_name = homework['lesson_name']
    if homework['status'] not in HOMEWORK_VERDICTS:
        logging.error('Статус не найден!')
        raise exceptions.StatusNotFoundException('Статус не найден!')
    verdict = HOMEWORK_VERDICTS[homework['status']]
    logging.info('Получен новый статус')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    logging.basicConfig(
        level=logging.DEBUG,
        format=LOG_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    if not check_tokens():
        print('Отсутствуют данные для авторизации')
        logging.critical('Отсутствуют данные для авторизации')
        raise exceptions.TokensNotFoundException('Проверьте данные в .env')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    # timestamp = int(time.time())
    current_timestamp = 0

    while True:
        try:
            logging.debug('Новый цикл опроса API стартовал')
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                homework = homeworks[0]
                message = parse_status(homework)
                print(message)
                send_message(bot, message)
            current_timestamp = response.get('current_date')
        except requests.exceptions.Timeout:
            send_message(bot, 'API timeout error')
        except requests.exceptions.ConnectionError:
            send_message(bot, 'API connection error')
        except requests.exceptions.HTTPError:
            send_message(bot, 'API HTTP error')
        except TypeError:
            send_message(bot, 'Ответ не является словарём')
        except exceptions.StatusNotFoundException:
            send_message(bot, 'Неизвестный статус')
        finally:
            logging.debug('Цикл опроса API завершён, засыпаю')
            time.sleep(10)


if __name__ == '__main__':
    main()
