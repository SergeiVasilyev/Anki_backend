from django.http import JsonResponse
from asgiref.sync import sync_to_async
from django.utils import timezone
from django.contrib.auth.hashers import check_password
from .models import CustomUser
from asgiref.sync import iscoroutinefunction, markcoroutinefunction
import asyncio
import re


# https://docs.djangoproject.com/en/5.1/topics/http/middleware/#asynchronous-support
class AsyncTokenAuthMiddleware:
    async_capable = True
    sync_capable = False

    def __init__(self, get_response):
        self.get_response = get_response
        if iscoroutinefunction(self.get_response):
            markcoroutinefunction(self)

    async def __call__(self, request):
        EXCLUDED_PATHS = [
            r'^/api/login/$',
            r'^/api/admin/',
            r'^/admin/',
        ]
        # Пропускаем проверку для исключенных URL
        if any(re.match(pattern, request.path) for pattern in EXCLUDED_PATHS):
            return await self._get_response(request)
        # if request.path in ['/api/login/', '/api/admin/', '/admin/', '/admin/login/']:
        #     return await self._get_response(request)

        # Получаем токен из заголовка
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header or not auth_header.startswith('Token '):
            return JsonResponse({'error': 'Token not provided'}, status=401)

        try:
            raw_token = auth_header.split(' ')[1]
            user = await self._get_user_by_token(raw_token)
            
            if not user:
                return JsonResponse({'error': 'Invalid or expired token'}, status=401)
            
            request.user = user
            return await self._get_response(request)
            
        except Exception as e:
            return JsonResponse({'error': f'Authentication failed: {str(e)}'}, status=400)

    async def _get_response(self, request):
        """Обработка следующего middleware/view"""
        response = self.get_response(request)
        return await response if asyncio.iscoroutine(response) else response

    async def _get_user_by_token(self, raw_token):
        """Асинхронный метод поиска пользователя по токену"""
        # Выносим импорты сюда, чтобы избежать циклических зависимостей
        from django.utils import timezone
        from django.contrib.auth.hashers import check_password
        from .models import CustomUser
        
        # Используем sync_to_async для выполнения синхронного ORM-запроса
        return await sync_to_async(self._sync_get_user_by_token, thread_sensitive=False)(raw_token)

    def _sync_get_user_by_token(self, raw_token):
        """Синхронная реализация поиска пользователя"""
        # return CustomUser.objects.filter(
        #     token_expires__gt=timezone.now(),
        #     token=raw_token  # Предполагаем, что token хранится в открытом виде
        # ).first()
        for user in CustomUser.objects.filter(token_expires__gt=timezone.now()):
            if check_password(raw_token, user.token):
                return user
        return None



# import asyncio
# from django.http import JsonResponse
# from asgiref.sync import sync_to_async
# from asgiref.sync import iscoroutinefunction, markcoroutinefunction

# class AsyncTokenAuthMiddleware:
#     async_capable = True
#     sync_capable = False

#     def __init__(self, get_response):
#         self.get_response = get_response
#         # self._is_coroutine = asyncio.iscoroutinefunction(get_response)
#         if iscoroutinefunction(self.get_response):
#             markcoroutinefunction(self)

#     async def __call__(self, request):
#         # Пропускаем проверку для исключенных URL
#         if request.path in ['/api/login/', '/api/admin/']:
#             return await self._get_response(request)

#         # Получаем токен из заголовка
#         auth_header = request.META.get('HTTP_AUTHORIZATION', '')
#         if not auth_header or not auth_header.startswith('Token '):
#             return JsonResponse({'error': 'Token not provided'}, status=401)

#         try:
#             raw_token = auth_header.split(' ')[1]
#             user = await self._get_user_by_token(raw_token)
            
#             if not user:
#                 return JsonResponse({'error': 'Invalid or expired token'}, status=401)
            
#             request.user = user
#             return await self._get_response(request)
            
#         except Exception as e:
#             return JsonResponse({'error': f'Authentication failed: {str(e)}'}, status=400)

#     async def _get_response(self, request):
#         """Обработка следующего middleware/view с гарантированным возвратом HttpResponse"""
#         response = await self.get_response(request)
#         return response

#     @sync_to_async
#     def _get_user_by_token(self, raw_token):
#         """Асинхронный метод поиска пользователя по токену"""
#         from django.utils import timezone
#         from django.contrib.auth.hashers import check_password
#         from .models import CustomUser

#         for user in CustomUser.objects.filter(token_expires__gt=timezone.now()):
#             if check_password(raw_token, user.token):
#                 return user
#         return None




# from django.http import JsonResponse
# from django.contrib.auth.hashers import check_password
# from django.utils import timezone
# from .models import CustomUser  # модель, где хранятся токены

# class TokenAuthMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         # Пропускаем проверку для некоторых URL (например, login)
#         if request.path in ['/api/login/', '/api/admin/']:
#             return self.get_response(request)
            
#         # Получаем токен из заголовка
#         auth_header = request.META.get('HTTP_AUTHORIZATION', '')
#         if not auth_header.startswith('Token '):
#             return JsonResponse({'error': 'Token not provided'}, status=401)
            
#         raw_token = auth_header.split(' ')[1]
        
#         # Ищем пользователя, у которого токен совпадает с переданным
#         user = None
#         for custom_user in CustomUser.objects.filter(token_expires__gt=timezone.now()):
#             if check_password(raw_token, custom_user.token):
#                 user = custom_user
#                 break
        
#         print(f"Found user: {user}")
#         if user:
#             print(f"Token match: {check_password(raw_token, user.token)}")
        
#         if not user:
#             return JsonResponse({'error': 'Invalid or expired token'}, status=401)
            
#         request.user = user
#         return self.get_response(request)