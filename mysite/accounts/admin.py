from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # 一覧画面
    list_display = ('username', 'email', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)

    # 編集画面にカスタムフィールドを追加
    fieldsets = UserAdmin.fieldsets + (
        ('プロフィール', {'fields': ('icon', 'introduction', 'followers')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('プロフィール', {'fields': ('email', 'icon', 'introduction')}),
    )
    filter_horizontal = ('followers', 'groups', 'user_permissions')
