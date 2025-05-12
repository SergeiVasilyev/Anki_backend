import re
import asyncio
from django.http import JsonResponse
from asgiref.sync import sync_to_async

def is_valid_email(email: str) -> bool:
    # Расширенное регулярное выражение, приближённое к RFC 5322
    pattern = r'''^(?:(?:[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*)|
                   (?:"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|
                   \\[\x01-\x09\x0b\x0c\x0e-\x7f])*"))@
                   (?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+
                   [a-zA-Z]{2,})$'''

    if not re.match(pattern, email, re.VERBOSE):
        return False

    try:
        local_part, domain = email.rsplit("@", 1)
    except ValueError:
        return False

    # Проверка на двойные точки
    if ".." in local_part or ".." in domain:
        return False

    # Проверка на длину
    if len(local_part) > 64 or len(domain) > 255:
        return False

    return True


def is_valid_password(password: str) -> bool:
    # Проверка длины
    if len(password) < 8:
        return False

    # Проверка наличия хотя бы одного "символа" (буквы, цифры или спецсимвола)
    if not re.search(r'\S', password):  # \S — любой непробельный символ
        return False

    return True


def check_auth(view_func):
    async def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        response = view_func(request, *args, **kwargs)
        return await response if asyncio.iscoroutine(response) else response
    return wrapper