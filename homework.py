"""Бот для проверки статуса домашних заданий."""
import logging
import os
import sys
import time

from http import HTTPStatus
from dotenv import load_dotenv

import requests
import telegram
import exceptions


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
    """Проверка наличия данных в .env."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Функция отправки сообщение в Telegram чат.
    определяемый переменной окружения TELEGRAM_CHAT_ID.
    Принимает на вход два параметра: экземпляр класса Bot
    и строку с текстом сообщения.
    """
    try:
        logging.debug('Попытка отправки в tg')
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logging.debug('Сообщение отправлено в tg')
    except telegram.error.TelegramError as exc:
        logging.error('Ошибка отправки в tg')
        raise exceptions.SendToBotException('Неудачная попытка') from exc


def get_api_answer(timestamp):
    """Функция запроса к единственному эндпоинту API-сервиса.
    В качестве параметра в функцию передается временная метка.
    В случае успешного запроса должна вернуть ответ API,
    приведя его из формата JSON к типам данных Python.
    """
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    payload = {'from_date': timestamp}
    try:
        logging.debug('Попытка запроса к API')
        response = requests.get(
            ENDPOINT,
            headers=headers,
            params=payload,
            timeout=10
        )
        logging.debug('Успешный запрос к API')
    except requests.exceptions.Timeout as exc:
        logging.error('API timeout')
        raise exceptions.GetAPIErrorException('API timeout') from exc
    except requests.exceptions.ConnectionError as exc:
        logging.error('API connection error')
        raise exceptions.GetAPIErrorException(
            'API connection error'
        ) from exc
    except requests.RequestException as exc:
        logging.error('API request error')
        raise exceptions.GetAPIErrorException(
            'API request error'
        ) from exc
    if response.status_code != HTTPStatus.OK:
        raise exceptions.GetAPIErrorException('API response not 200')
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
    except KeyError as exc:
        logging.error('В ответе API отсутствует ключ "homeworks"')
        raise exceptions.ResponseFormatException(
            'В ответе API отсутствует ключ "homeworks"'
        ) from exc
    if not isinstance(homeworks_list, list):
        logging.error('Неверный формат ответа о работе')
        raise TypeError('Неверный формат ответа о работе')
    if not homeworks_list:
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
    except KeyError as exc:
        logging.error('В ответе API тсуствует ключ "homework_name"')
        raise exceptions.ParseErrorException(
            'Отсутствует ключ с именем работы'
        ) from exc
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
        logging.critical('Отсутствуют данные для авторизации')
        raise exceptions.TokensNotFoundException('Проверьте данные в .env')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    # ноль был, чтобы бот подавал признаки жизни на время отладки :)
    current_timestamp = int(time.time())
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
