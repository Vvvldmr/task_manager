from django.db import models
from django.conf import settings
from django.utils import timezone


class Status(models.TextChoices):
    TODO = "todo", "К выполнению"
    DOING = "doing", "В процессе"
    DONE = "done", "Выполнено"


class Priority(models.IntegerChoices):
    LOW = 1, "Низкий"
    MEDIUM = 2, "Средний"
    HIGH = 3, "Высокий"


class Task(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    deadline = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO)
    priority = models.IntegerField(choices=Priority.choices, default=Priority.MEDIUM)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tasks")

    def save(self, *args, **kwargs):
        if self.status == Status.DONE and self.completed_at is None:
            self.completed_at = timezone.now()
        elif self.status != Status.DONE:
            self.completed_at = None

        super().save(*args, **kwargs)


    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-priority", "deadline", "-created_at"]


class Friendship(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friendships",
    )

    friend = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friendships_as_friend",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "friend"],
                name="unique_friendship",
            ),
        ]


class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Комментарий от {self.author} к «{self.task}»"


class FriendRequest(models.Model):
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_friend_requests",
    )

    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_friend_requests",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["from_user", "to_user"],
                name="unique_friend_request",
            ),
        ]

    def __str__(self):
        return f"Заявка от {self.from_user} к {self.to_user}"