from django.db import models

# Create your models here.

from django.utils import timezone
from accounts.models import User


class Post(models.Model):
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, verbose_name='author',
                               on_delete=models.CASCADE)
    likes = models.IntegerField(default=0)

    def __str__(self):
        return self.content


class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
