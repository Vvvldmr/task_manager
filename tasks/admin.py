from django.contrib import admin

from .models import Task, Friendship, Comment, FriendRequest


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "status", "priority", "deadline", "created_at")
    list_filter = ("status", "priority")
    search_fields = ("name", "description", "owner__username")


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ("user", "friend", "created_at")
    search_fields = ("user__username", "friend__username")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("task", "author", "created_at")
    search_fields = ("text", "author__username", "task__name")


@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ("from_user", "to_user", "created_at")
    search_fields = ("from_user__username", "to_user__username")
