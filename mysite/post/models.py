from django.db import models

# Create your models here.
from django.contrib.auth import get_user_model


class Post(models.Model):
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(get_user_model(), verbose_name='author',
                               on_delete=models.CASCADE)

    def __str__(self):
        return self.content
