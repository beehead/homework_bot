"""Собственные исключения."""


class TokensNotFoundException(Exception):
    """Отсутствует данные в .env"""


class StatusNotFoundException(Exception):
    """Статус отсуствует в ответе"""
