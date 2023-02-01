"""Собственные исключения."""


class TokensNotFoundException(Exception):
    """Отсутствует данные в env."""


class StatusNotFoundException(Exception):
    """Статус отсуствует в ответе."""


class SendToBotException(Exception):
    """Проблема отправки сообщения в tg."""


class GetAPIErrorException(Exception):
    """Проблема с получением данных по API."""


class ParseErrorException(Exception):
    """Проблема с разбором ответа от API."""
