from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.forms import ModelForm
from django import forms
from django.shortcuts import get_object_or_404


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['placeholder'] = field.label
            field.widget.attrs['class'] = 'form-control'


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = UserCreationForm.Meta.fields + ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['placeholder'] = field.label
            field.widget.attrs['class'] = 'form-control'


class UserChangeForm(ModelForm):
    class Meta:
        model = get_user_model()
        fields = (
            'username',
            'email',
            'introduction',
        )

    def __init__(self, *args, username=None, email=None, introduction=None, **kwargs):
        kwargs.setdefault('label_suffix', '')
        if username:
            # 既存ユーザーを instance として渡すことで ModelForm が初期値を自動設定する
            kwargs['instance'] = get_object_or_404(get_user_model(), username=username)
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['placeholder'] = field.label
            field.widget.attrs['class'] = 'form-control'

    def update(self, user):
        """変更があったフィールドのみ保存する。変更なしの場合は DB アクセスしない。"""
        fields = []
        if user.username != self.cleaned_data['username']:
            user.username = self.cleaned_data['username']
            fields.append('username')
        if user.email != self.cleaned_data['email']:
            user.email = self.cleaned_data['email']
            fields.append('email')
        if user.introduction != self.cleaned_data['introduction']:
            user.introduction = self.cleaned_data['introduction']
            fields.append('introduction')
        if fields:
            user.save(update_fields=fields)


class UserPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['placeholder'] = field.label
            field.widget.attrs['class'] = 'form-control'


class UploadProfileImgForm(forms.Form):
    """プロフィールアイコンのアップロードフォーム。"""
    icon = forms.ImageField(label="アイコン画像")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['placeholder'] = field.label
            field.widget.attrs['class'] = 'form-control'


# 後方互換エイリアス（既存コードが UpLoadProfileImgForm を参照している箇所に対応）
UpLoadProfileImgForm = UploadProfileImgForm
