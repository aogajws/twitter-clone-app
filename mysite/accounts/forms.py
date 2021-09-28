from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User
from django.forms import ModelForm


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        for field in self.fields.values():
            field.widget.attrs['placeholder'] = field.label


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = User
        fields = UserCreationForm.Meta.fields + ("email",)


class UserChangeForm(ModelForm):
    class Meta:
        model = User
        fields = (
            'username',
            'email',
        )

    def __init__(self, username=None, email=None, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super().__init__(*args, **kwargs)
        # ユーザーの更新前情報をフォームに挿入
        if username:
            self.fields['username'].widget.attrs['value'] = username
        if email:
            self.fields['email'].widget.attrs['value'] = email

    def update(self, user):
        if user.username != self.cleaned_data['username']:
            user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        user.save()
