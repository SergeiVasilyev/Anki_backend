from django.core.exceptions import ValidationError
from django.core.validators import validate_email


class UserSerializer:
    @staticmethod
    def serialize_user(user):
        return {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'last_login': user.last_login.isoformat(),
            'token_expires': user.token_expires.isoformat()
        }
    
    @staticmethod
    def validate_email(email):
        try:
            validate_email(email)
            return True
        except ValidationError:
            return False

class SetSerializer:
    @staticmethod
    def serialize_set(card_set):
        return {
            'id': card_set.id,
            'title': card_set.title,
            'description': card_set.description,
            'term_lang': card_set.term_lang,
            'definition_lang': card_set.definition_lang,
            'created_at': card_set.created_at.isoformat(),
            'is_public': card_set.is_public,
            # 'cards': [CardSerializer.serialize_card(card) for card in card_set.cards.all()],
            'user': UserSerializer.serialize_user(card_set.user)
        }


class CardSerializer:
    @staticmethod
    def serialize_card(card):
        return {
            'id': card.id,
            'term': card.term,
            'definition': card.definition,
            'set': card.set.id,
            'image_url': card.image_url,
            'audio_url': card.audio_url
        }