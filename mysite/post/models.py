from django.db import models

# Create your models here.

from django.utils import timezone
from django.contrib.auth import get_user_model


class Post(models.Model):
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(get_user_model(), verbose_name='author',
                               on_delete=models.CASCADE)
    parent = models.ForeignKey('self', blank=True, null=True, related_name='replies',
                               on_delete=models.CASCADE)

    def __str__(self):
        return self.content


class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
