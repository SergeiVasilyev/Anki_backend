from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth.hashers import make_password
import secrets


class CustomUser(AbstractUser):
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    token_id = models.CharField(max_length=32, null=True, blank=True, db_index=True)
    token = models.TextField(blank=True, null=True)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(default=timezone.now)
    token_expires = models.DateTimeField(default=timezone.now)

    # Указываем уникальные related_name для groups и user_permissions
    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name="groups",
        blank=True,
        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
        related_name="customuser_groups",  # Уникальное имя для обратной связи
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name="user permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        related_name="customuser_permissions",  # Уникальное имя для обратной связи
        related_query_name="customuser",
    )

    def generate_token_pair(self):
        token_id = secrets.token_hex(8)  # 16 символов
        token_secret = secrets.token_urlsafe(32)
        full_token = f"{token_id}:{token_secret}"
        token_hash = make_password(token_secret)
        self.token_expires = timezone.now() + timedelta(days=2)
        self.token_id = token_id
        self.token = token_hash
        self.save()
        return full_token, token_id, token_hash

    def generate_token(self):
        raw_token = secrets.token_hex(32)
        self.token = make_password(raw_token)
        # self.token = make_password(raw_token, hasher='pbkdf2_sha256_iterations=100000') # Используем pbkdf2_sha256, уменьшенное количество итераций
        self.token_expires = timezone.now() + timedelta(days=2)
        self.save()
        return raw_token
    
    async def async_generate_token(self):
        raw_token = secrets.token_hex(32)
        self.token = make_password(raw_token, hasher='pbkdf2_sha256_custom')
        self.token_expires = timezone.now() + timedelta(days=2)
        await self.asave()  # <--- async save
        return raw_token
    
    def generate_token2(self):
        import secrets
        import hashlib
        from django.utils import timezone
        from datetime import timedelta
        # Генерируем достаточно случайный токен (32 байта -> 64 hex символа)
        raw_token = secrets.token_urlsafe(32)  # Быстрее чем token_hex и URL-safe
        
        # Быстрый хеш вместо make_password (используем SHA256)
        self.token = hashlib.sha256(raw_token.encode()).hexdigest()
        
        # Устанавливаем срок действия
        self.token_expires = timezone.now() + timedelta(days=2)
        
        # Оптимизированное сохранение (только нужные поля)
        self.save(update_fields=['token', 'token_expires'])
        
        return raw_token
    
    def is_token_valid(self):
        return self.token_expires and self.token_expires > timezone.now()
    
    
    def update_last_login(self):
        self.last_login = timezone.now()
        self.save()
    
    class Meta:
        verbose_name = 'Custom User'
        verbose_name_plural = 'Custom Users'

    def __str__(self):
        return self.username


# 2. Sets
class Set(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="sets")
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    term_lang = models.CharField(max_length=50, null=True, blank=True)
    definition_lang = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return self.title


# 3. Cards
class Card(models.Model):
    set = models.ForeignKey(Set, on_delete=models.CASCADE, related_name="cards")
    term = models.TextField()
    definition = models.TextField() # TODO  add blank=True
    image_url = models.URLField(blank=True, null=True)
    audio_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.term} - {self.definition}"
    

# 4. Learning Progress
class LearningProgress(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="learning_progress")
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="learning_progress")
    level = models.IntegerField(default=0)  # Уровень от 0 до 5
    last_reviewed = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "card")

    def __str__(self):
        return f"{self.user.username} - {self.card.term} (Level {self.level})"
    

# 4. Rooms
class Room(models.Model):
    creator = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="rooms_created")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


# 5. Room Members
class RoomMember(models.Model):
    room_obj = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("room_obj", "user")

    def __str__(self):
        return f"{self.user.username} in {self.room_obj.name}"


# 6. Quizzes
class Quiz(models.Model):
    set = models.ForeignKey(Set, on_delete=models.CASCADE, related_name="quizzes")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title


# 7. Quiz Results
class QuizResult(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="results")
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="quiz_results")
    score = models.IntegerField()
    total = models.IntegerField()
    completed_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.score}/{self.total}"


# 8. Notifications
class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.message[:50]  # Показываем первые 50 символов


# 9. Friends
class Friend(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="friends")
    friend = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="friend_of")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "friend")

    def __str__(self):
        return f"{self.user.username} -> {self.friend.username} ({self.status})"


# 10. Likes and Saves
class LikeSave(models.Model):
    ACTION_CHOICES = [
        ("like", "Like"),
        ("save", "Save"),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="likes_saves")
    set = models.ForeignKey(Set, on_delete=models.CASCADE, related_name="likes_saves")
    action_type = models.CharField(max_length=10, choices=ACTION_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("user", "set", "action_type")

    def __str__(self):
        return f"{self.user.username} {self.action_type}d {self.set.title}"