import re
from fastapi import FastAPI, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse
from anki_quiz.models import CustomUser, Set, Card
from anki_quiz.serializers import CardSerializer, UserSerializer, SetSerializer
from asgiref.sync import sync_to_async
from django.contrib.auth.hashers import check_password
from django.db import transaction
from typing import Dict, Any
from datetime import datetime, timezone
from typing import List, Union
from functools import wraps

api_app = FastAPI()


@api_app.middleware("http")
async def check_auth(request: Request, call_next):
    EXCLUDED_PATHS = [
        r'^/api/login/$',
        r'^/api/admin/',
        r'^/api/register/',
        r'^/api/check-auth/',
        r'^/api/users/',
    ]

    if any(re.match(pattern, request.url.path) for pattern in EXCLUDED_PATHS):
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Token "):
        return JSONResponse({"success": False, "error": "Token not provided"}, status_code=401)

    try:
        token = auth_header.split(" ")[1]
        token_id, token_secret = token.split(":")
    except ValueError:
        return JSONResponse({"success": False, "error": "Invalid token format"}, status_code=400)

    try:
        user = await sync_to_async(CustomUser.objects.get)(token_id=token_id)
    except CustomUser.DoesNotExist:
        return JSONResponse({"success": False, "error": "Invalid token"}, status_code=401)

    if check_password(token_secret, user.token):
        request.state.user = user
        return await call_next(request)

    return JSONResponse({"success": False, "error": "Invalid token"}, status_code=401)




@api_app.get("/ping")
async def ping():
    return {"message": "pong"}

@api_app.get("/users/{email}")
async def get_user(email: str):
    try:
        user = await sync_to_async(CustomUser.objects.get)(email=email)
        return {"email": user.email, "name": user.username}
    except CustomUser.DoesNotExist:
        return {"error": "User not found"}

@api_app.get("/users/")
async def get_users():
    users = await sync_to_async(list)(CustomUser.objects.all())
    return [{"email": user.email, "name": user.username} for user in users]


# -------------------Authentication-----------------
@api_app.post("/login/")
async def login(payload: Dict[Any, Any]):
    email = payload.get("email")
    password = payload.get("password")

    try:
        user = await sync_to_async(CustomUser.objects.get)(email=email)
    except CustomUser.DoesNotExist:
        return {"success": False, "error": "Invalid credentials"}

    if not user.check_password(password):
        return {"success": False, "error": "Invalid credentials"}

    if user:
        # token = await sync_to_async(user.generate_token)()
        full_token, _, _ = await sync_to_async(user.generate_token_pair)()
        user_data = await sync_to_async(UserSerializer.serialize_user)(user)
        return {"success": True, "token": full_token, "user": user_data, "expires": user.token_expires.isoformat()}
    else:
        return {"success": False, "error": "Invalid credentials"}
    

@api_app.post("/register/")
async def register(payload: Dict[Any, Any]):
    email = payload.get("email")
    password = payload.get("password")
    name = payload.get("name")

    if not UserSerializer.validate_email(email):
        return {"success": False, "error": "Invalid email"}
    
    user_exists = await CustomUser.objects.filter(email=email).aexists()
    if user_exists:
        return {"success": False, "error": "Email already exists"}

    user = await sync_to_async(CustomUser.objects.create_user)(email=email, username=email, password=password, name=name)
    full_token, _, _ = await sync_to_async(user.generate_token_pair)()
    user_data = await sync_to_async(UserSerializer.serialize_user)(user)
    return {"success": True, "token": full_token, "user": user_data, "expires": user.token_expires.isoformat()}


@api_app.post("/check-auth/")
async def check_auth(request: Request, response: Response):
    auth_header = request.headers.get("Authorization")
    token = None
    response.status_code = 400

    if auth_header and auth_header.startswith('Token '):
        token = auth_header.split(' ', 1)[1]
    else:
        return {"success": False, "error": "Token not provided"}
    
    try:
        token_id, token_secret = token.split(":")
    except ValueError:
        return {"success": False, "error": "Invalid token"}
    
    try:
        user = await sync_to_async(CustomUser.objects.get)(token_id=token_id)
    except CustomUser.DoesNotExist:
        return {"success": False, "error": "Invalid token"}
    
    if check_password(token_secret, user.token):
        response.status_code = 200
        return {"success": True, "user": UserSerializer.serialize_user(user)}

    return {"success": False, "error": "Invalid token"}

# ------------------End Authentication---------------


# ------------------Sets------------------

@api_app.post("/create-set/")
async def create_set(request: Request, response: Response):
    data = await request.json()
    user = request.state.user
    response.status_code = 400

    if user:
        try:
            new_set = await sync_to_async(Set.objects.create)(user=user, **data)
            response.status_code = 200
            return {"success": True, "set": await sync_to_async(SetSerializer.serialize_set)(new_set)}
        except Exception as e:
            print('Create set error:', e)
            return {"success": False, "error": "Error creating set, invalid data format (title, description, is_public) or user not found"}

    return {"success": False, "error": "User not found"}


@api_app.get("/get-sets/")
async def get_sets(
        request: Request, 
        response: Response, 
        since: str = '1999-01-01T00:00:00',
        skip: int = Query(0, ge=0, description="Number of items to skip"),
        limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return")   
    ):

    user = request.state.user
    response.status_code = 400
    
    if user:
        try:
            sets_query = Set.objects.filter(user=user).filter(created_at__gt=since).order_by('-created_at')[skip:skip+limit+1] # прибавляем 1, чтобы узнать, есть ли еще данные
            sets = await sync_to_async(list)(sets_query)

            # Проверяем, есть ли еще данные
            has_more = len(sets) > limit
            if has_more:
                sets = sets[:limit]  # Обрезаем лишнее

            response.status_code = 200
            return {"success": True, 
                    "sets": [await sync_to_async(SetSerializer.serialize_set)(set) for set in sets], 
                    "pagination": {
                    "skip": skip,
                    "limit": limit,
                    "count": len(sets),
                    "has_more": has_more
                }
            }
        except Exception as e:
            print('Get sets error:', e)
            return {"success": False, "error": "Error getting sets"}

    return {"success": False, "error": "User not found"}


@api_app.get("/get-set/{set_id}/")
async def get_set(request: Request, response: Response, set_id: int):
    user = request.state.user
    response.status_code = 400

    if user:
        try:
            set = await sync_to_async(Set.objects.get)(id=set_id, user=user)
            response.status_code = 200
            return {"success": True, "set": await sync_to_async(SetSerializer.serialize_set)(set)}
        except Exception as e:
            print('Get set error:', e)
            return {"success": False, "error": "Error getting set, user not found or set not found"}

    return {"success": False, "error": "User not found"}


@api_app.post("/update-set/{set_id}/")
async def update_set(request: Request, response: Response, set_id: int):
    data = await request.json()
    user = request.state.user
    response.status_code = 400

    if user:
        try:
            set = await sync_to_async(Set.objects.get)(id=set_id, user=user)
            set.title = data.get("title", set.title)
            set.description = data.get("description", set.description)
            set.is_public = data.get("is_public", set.is_public)
            await sync_to_async(set.save)()
            response.status_code = 200
            return {"success": True, "set": await sync_to_async(SetSerializer.serialize_set)(set)}
        except Exception as e:
            print('Update set error:', e)
            return {"success": False, "error": "Error updating set, user not found or set not found"}

    return {"success": False, "error": "User not found"}


@api_app.delete("/delete-set/{set_id}/") # TODO test this
async def delete_set(request: Request, response: Response, set_id: int):
    user = request.state.user
    response.status_code = 400

    if user:
        try:
            set = await sync_to_async(Set.objects.get)(id=set_id, user=user)
            await sync_to_async(set.delete)()
            response.status_code = 200
            return {"success": True, "message": "Set deleted successfully"}
        except Exception as e:
            print('Delete set error:', e)
            return {"success": False, "error": "Error deleting set, user not found or set not found"}

    return {"success": False, "error": "User not found"}


# -------------------End of Sets-------------------


#--------------------Cards routes--------------------

@api_app.get("/get-cards/{set_id}/")
async def get_cards(request: Request, response: Response, set_id: int):
    user = request.state.user
    response.status_code = 400

    if user:
        try:
            cards = await sync_to_async(list)(Card.objects.filter(set__user=user, set__id=set_id))
            response.status_code = 200
            return {"success": True, "cards": [await sync_to_async(CardSerializer.serialize_card)(card) for card in cards]}
        except Exception as e:
            print('Get cards error:', e)
            return {"success": False, "error": "Error getting cards, user not found"}

    return {"success": False, "error": "User not found"}







# Декоратор для синхронных Django ORM операций
def django_db_sync_to_async(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await sync_to_async(func)(*args, **kwargs)
    return wrapper

@django_db_sync_to_async
def check_set_exists(set_id: int, user_id: int) -> bool:
    return Set.objects.filter(id=set_id, user_id=user_id).exists()

@django_db_sync_to_async
def process_cards_in_transaction(set_id: int, cards_data: List[dict]) -> List[Card]:
    with transaction.atomic():
        results = []
        for card_data in cards_data:
            card_id = card_data.get('id')
            if card_id:
                # Обновление существующей карточки
                card = Card.objects.filter(id=card_id, set_id=set_id).first()
                if not card:
                    raise ValueError(f"Card with ID {card_id} not found")
                
                card.term = card_data.get('term', card.term)
                card.definition = card_data.get('definition', card.definition)
                card.image_url = card_data.get('image_url', card.image_url)
                card.audio_url = card_data.get('audio_url', card.audio_url)
                card.save()
            else:
                # Создание новой карточки
                card = Card.objects.create(
                    set_id=set_id,
                    term=card_data['term'],
                    definition=card_data['definition'],
                    image_url=card_data.get('image_url'),
                    audio_url=card_data.get('audio_url')
                )
            results.append(card)
        return results

@django_db_sync_to_async
def serialize_cards(cards: List[Card]) -> List[dict]:
    return [CardSerializer.serialize_card(card) for card in cards]

@api_app.post("/create-update-cards/{set_id}/", status_code=200)
async def create_update_cards(
    request: Request,
    set_id: int,
    response: Response
):
    try:
        # Проверка существования набора
        if not await check_set_exists(set_id, request.state.user.id):
            response.status_code = 404
            return {"success": False, "error": "Set not found"}

        data = await request.json()
        if not data.get('cards'):
            response.status_code = 400
            return {"success": False, "error": "No cards provided"}

        # Обработка карточек в транзакции
        cards = await process_cards_in_transaction(set_id, data['cards'])
        
        # Сериализация результатов
        serialized_cards = await serialize_cards(cards)
        
        return {
            "success": True,
            "cards": serialized_cards
        }

    except ValueError as e:
        response.status_code = 404
        return {"success": False, "error": str(e)}
    except Exception as e:
        response.status_code = 400
        return {"success": False, "error": f"Processing error: {str(e)}"}



    




@api_app.post("/create-card/")
async def create_card(request: Request, response: Response):
    data = await request.json()
    user = request.state.user
    response.status_code = 400

    if user:
        try:
            data["set"] = await sync_to_async(Set.objects.get)(id=data.get("set"), user=user)
            new_card = await sync_to_async(Card.objects.create)(**data)
            response.status_code = 200
            return {"success": True, "card": await sync_to_async(CardSerializer.serialize_card)(new_card)}
        except Exception as e:
            print('Create card error:', e)
            return {"success": False, "error": "Error creating card, invalid data format (term, definition, set) or user not found"}

    return {"success": False, "error": "User not found"}



@api_app.get("/get-card/{card_id}/")
async def get_card(request: Request, response: Response, card_id: int):
    user = request.state.user
    response.status_code = 400

    if user:
        try:            
            card = await sync_to_async(Card.objects.get)(id=card_id, set__user=user)
            response.status_code = 200
            return {"success": True, "card": await sync_to_async(CardSerializer.serialize_card)(card)}
        except Exception as e:
            print('Get card error:', e)
            return {"success": False, "error": "Error getting card, user not found or card not found"}

    return {"success": False, "error": "User not found"}


@api_app.post("/update-card/{card_id}/")
async def update_card(request: Request, response: Response, card_id: int):
    data = await request.json()
    user = request.state.user
    response.status_code = 400

    if user:
        try:
            card = await sync_to_async(Card.objects.get)(id=card_id, set__user=user)
            card.term = data.get("term", card.term)
            card.definition = data.get("definition", card.definition)
            await sync_to_async(card.save)()
            response.status_code = 200
            return {"success": True, "card": await sync_to_async(CardSerializer.serialize_card)(card)}
        except Exception as e:
            print('Update card error:', e)
            return {"success": False, "error": "Error updating card, user not found or card not found"}

    return {"success": False, "error": "User not found"}


@api_app.delete("/delete-card/{card_id}/")
async def delete_card(request: Request, response: Response, card_id: int):
    user = request.state.user
    response.status_code = 400

    if user:
        try:
            card = await sync_to_async(Card.objects.get)(id=card_id, set__user=user)
            await sync_to_async(card.delete)()
            response.status_code = 200
            return {"success": True, "message": "Card deleted successfully"}
        except Exception as e:
            print('Delete card error:', e)
            return {"success": False, "error": "Error deleting card, user not found or card not found"}

    return {"success": False, "error": "User not found"}





