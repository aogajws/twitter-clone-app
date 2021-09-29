from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User
from django.forms import ModelForm
from django import forms


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        for field in self.fields.values():
            field.widget.attrs['placeholder'] = field.label


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)


class UserChangeForm(ModelForm):
    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'introduction',
        )

    def __init__(self, username=None, email=None, introduction=None, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super().__init__(*args, **kwargs)
        # ユーザーの更新前情報をフォームに挿入
        if username:
            self.fields['username'].widget.attrs['value'] = username
        if email:
            self.fields['email'].widget.attrs['value'] = email
        if introduction:
            self.fields['introduction'].widget.attrs['value'] = introduction

    def update(self, user):
        if user.username != self.cleaned_data['username']:
            user.username = self.cleaned_data['username']
        if user.email != self.cleaned_data['email']:
            user.email = self.cleaned_data['email']
        if user.introduction != self.cleaned_data['introduction']:
            user.introduction = self.cleaned_data['introduction']
        user.save()


class UpLoadProfileImgForm(forms.Form):
    icon = forms.ImageField()
