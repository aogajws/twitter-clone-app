from django import forms
from .models import Post


class PostCreationForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('content',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
