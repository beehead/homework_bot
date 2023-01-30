"""Собственные исключения"""


class TokensNotFoundException(Exception):
    """Отсутствует данные в .env"""
    pass


class StatusNotFoundException(Exception):
    """Статус отсуствует в ответе"""
    pass