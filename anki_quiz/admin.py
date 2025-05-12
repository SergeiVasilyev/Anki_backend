from django.contrib import admin
from .models import Set, Card, LearningProgress, CustomUser, LikeSave, Friend, Quiz, QuizResult, Room, RoomMember, Notification

@admin.register(Set)
class SetAdmin(admin.ModelAdmin):
    list_display = ("title", "description")

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("term", "definition", "set")

@admin.register(LearningProgress)
class LearningProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "card", "level", "last_reviewed")

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("username", "email")

@admin.register(LikeSave)
class LikeSaveAdmin(admin.ModelAdmin):
    list_display = ("user", "set", "action_type", "created_at")

@admin.register(Friend)
class FriendAdmin(admin.ModelAdmin):
    list_display = ("user", "friend", "status", "created_at")

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("set", "user", "title", "created_at")

@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = ("quiz", "user", "score", "total", "completed_at")

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("creator", "name", "description", "created_at")

@admin.register(RoomMember)
class RoomMemberAdmin(admin.ModelAdmin):
    list_display = ("room_obj", "user")

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "created_at")