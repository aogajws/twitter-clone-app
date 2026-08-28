from django.contrib import admin
from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    # 一覧画面
    list_display = ('id', 'author', 'short_content', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('content', 'author__username')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

    # 外部キーを raw_id フィールドにして大量データでも軽快に動作させる
    raw_id_fields = ('author', 'parent', 'repost_parent')
    filter_horizontal = ('liked_users',)

    @admin.display(description='本文（先頭50文字）')
    def short_content(self, obj):
        return obj.content[:50]
