from django.db import models
from django.contrib.auth import get_user_model


class Post(models.Model):
    content = models.TextField("本文")
    created_at = models.DateTimeField("投稿日時", auto_now_add=True)
    author = models.ForeignKey(
        get_user_model(),
        verbose_name="投稿者",
        on_delete=models.CASCADE,
    )
    parent = models.ForeignKey(
        'self',
        verbose_name="返信元投稿",
        blank=True,
        null=True,
        related_name='replies',
        on_delete=models.SET_NULL,
    )
    liked_users = models.ManyToManyField(
        get_user_model(),
        verbose_name="いいねしたユーザー",
        related_name='favorite_posts',
        blank=True,
    )
    repost_parent = models.ForeignKey(
        'self',
        verbose_name="リツイート元投稿",
        blank=True,
        null=True,
        related_name='reposted',
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = "投稿"
        verbose_name_plural = "投稿"
        ordering = ['-created_at']

    def __str__(self):
        return self.content[:50]
