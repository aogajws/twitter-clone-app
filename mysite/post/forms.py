from django import forms
from .models import Post

# ツイートの最大文字数
POST_MAX_LENGTH = 280


class PostCreationForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('content',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['placeholder'] = "いまどうしてる？"
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['maxlength'] = POST_MAX_LENGTH
