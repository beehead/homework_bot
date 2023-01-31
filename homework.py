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

logging.basicConfig(
    level=logging.DEBUG,
    format=LOG_FORMAT,
    handlers=[logging.StreamHandler(sys.stdout)]
)


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка наличия данных в .env."""
    return None not in (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)


def send_message(bot, message):
    """Функция отправки сообщение в Telegram чат.
    определяемый переменной окружения TELEGRAM_CHAT_ID.
    Принимает на вход два параметра: экземпляр класса Bot
    и строку с текстом сообщения.
    """
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logging.debug('Сообщение отправлено в tg')
    except telegram.error.TelegramError:
        logging.error('Ошибка отправки в tg')


def get_api_answer(timestamp):
    """Функция запроса к единственному эндпоинту API-сервиса.
    В качестве параметра в функцию передается временная метка.
    В случае успешного запроса должна вернуть ответ API,
    приведя его из формата JSON к типам данных Python.
    """
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
    except requests.RequestException:
        logging.error('API request error')
    if response.status_code != 200:
        raise requests.exceptions.HTTPError(response.status_code)
    return response.json()


def check_response(response):
    """Функция проверки ответа на соответствие документации.
    В качестве параметра функция получает ответ API,
    приведенный к типам данных Python.
    """
    if not isinstance(response, dict):
        logging.error('Ответ не является словарём')
        raise TypeError('Ответ не является словарём')
    try:
        homeworks_list = response['homeworks']
    except KeyError:
        logging.error('В ответе API отсутствует ключ "homeworks"')
    if not isinstance(homeworks_list, list):
        logging.error('Неверный формат ответа о работе')
        raise TypeError('Неверный формат ответа о работе')
    if homeworks_list == []:
        logging.debug('Новые статусы отсутствуют')
        return None
    logging.debug('Ответ получен, требуется анализ')
    return homeworks_list


def parse_status(homework):
    """Функция проверки ответа от Y.
    извлекает из информации о конкретной домашней работе
    статус этой работы. В качестве параметра функция получает
    только один элемент из списка домашних работ.
    В случае успеха, функция возвращает подготовленную для отправки
    в Telegram строку, содержащую один из вердиктов словаря
    HOMEWORK_VERDICTS.
    """
    try:
        homework_name = homework['homework_name']
    except KeyError:
        logging.error('В ответе API тсуствует ключ "homework_name"')
    if homework['status'] not in HOMEWORK_VERDICTS:
        logging.error('Статус не найден!')
        raise exceptions.StatusNotFoundException('Статус не найден!')
    verdict = HOMEWORK_VERDICTS[homework['status']]
    logging.info('Получен новый статус')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        print('Отсутствуют данные для авторизации')
        logging.critical('Отсутствуют данные для авторизации')
        raise exceptions.TokensNotFoundException('Проверьте данные в .env')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    # timestamp = int(time.time())
    current_timestamp = 0
    bot_last_error = ''

    while True:
        try:
            logging.debug('Новый цикл опроса API стартовал')
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                homework = homeworks[0]
                message = parse_status(homework)
                send_message(bot, message)
            current_timestamp = response.get('current_date')
        except Exception as error:
            message = f'Возникла ошибка: {error}'
            if message != bot_last_error:
                send_message(bot, message)
                bot_last_error = message
        finally:
            logging.debug('Цикл опроса API завершён, засыпаю')
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
