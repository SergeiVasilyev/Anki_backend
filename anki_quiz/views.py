from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .serializers import UserSerializer
from .models import CustomUser
from services.auth_services import is_valid_email, is_valid_password, check_auth
from asgiref.sync import sync_to_async
from django.contrib.auth.hashers import check_password
import logging

logger = logging.getLogger(__name__)

def main(request):
    return JsonResponse({'success': True, 'message': 'Main page'})


# --------------------------------- Basic auth ------------------------------------
@csrf_exempt
async def register_view(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST allowed'}, status=405)

    try:
        # Получение тела запроса
        data = json.loads(request.body)

        email = data['email']
        password = data['password']
        name = data['name']

        # Валидация email и пароля (если они sync-функции, обернём)
        if not await sync_to_async(is_valid_email)(email):
            print('Invalid email')
            return JsonResponse({'success': False, 'error': 'Email must be in the format "email@domain.com"'}, status=400)

        if not await sync_to_async(is_valid_password)(password):
            print('Invalid password')
            return JsonResponse({'success': False, 'error': 'Invalid password, must be at least 8 characters and contain at least one letter'}, status=400)

        # Проверка на существование email
        user_exists = await CustomUser.objects.filter(email=email).aexists()
        if user_exists:
            print('Email already exists')
            return JsonResponse({'success': False, 'error': 'Email already exists'}, status=400)

        # Создание пользователя (если .create_user синхронный — оборачиваем)
        user = await sync_to_async(CustomUser.objects.create_user)(
            email=email,
            username=email,
            password=password,
            name=name
        )

        # Генерация токена (если метод синхронный)
        token = await sync_to_async(user.generate_token)()
        print('token', token)

        return JsonResponse({
            'success': True,
            'token': token,
            'user': await sync_to_async(UserSerializer.serialize_user)(user),
            'expires': user.token_expires.isoformat()
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)



@csrf_exempt
async def login_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = await CustomUser.objects.filter(email=data['email']).afirst()

            if not user.check_password(data['password']):
                return JsonResponse({'success': False, 'error': 'Invalid credentials'}, status=401)
            
            if user:
                token = await user.async_generate_token()
                
                return JsonResponse({
                    'success': True,
                    'token': token,
                    'user': UserSerializer.serialize_user(user),
                    'expires': user.token_expires.isoformat()
                })
            
            return JsonResponse({'success': False, 'error': 'Invalid credentials'}, status=401)

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
async def check_auth_view(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        # data = json.loads(request.body)
        # token = data.get('token')

        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Token '):
            token = auth_header.split(' ', 1)[1]

        if not token:
            return JsonResponse({'success': False, 'error': 'Token required'}, status=400)

        # Ищем пользователей с токеном (непустым)
        users = await sync_to_async(list)(
            CustomUser.objects.exclude(token__isnull=True).exclude(token__exact='')
        )

        # Перебираем и ищем совпадение по хэшу
        for user in users:
            if await sync_to_async(check_password)(token, user.token):
                # Проверка срока действия
                is_valid = await sync_to_async(user.is_token_valid)()
                if not is_valid:
                    return JsonResponse({'success': False, 'error': 'Token expired'}, status=401)

                user_data = await sync_to_async(UserSerializer.serialize_user)(user)
                return JsonResponse({
                    'success': True,
                    'user': user_data,
                })

        return JsonResponse({'success': False, 'error': 'Invalid token'}, status=401)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Check auth error: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)

# --------------------------------End of Basic auth --------------------------------