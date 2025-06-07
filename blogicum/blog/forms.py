from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm
from django.utils import timezone

from .models import Post, Comment

User = get_user_model()


class EditProfileForm(UserChangeForm):
    password = None

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        labels = {
            'username': 'Логин',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Email'
        }
        widgets = {
            'email': forms.EmailInput(attrs={'required': True})
        }


class PostCreateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = (
            'title',
            'text',
            'pub_date',
            'image',
            'category',
            'location',
            'is_published'
        )
        widgets = {
            'pub_date': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control'
                },
                format='%Y-%m-%dT%H:%M'
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # Только для нового поста
            self.initial['pub_date'] = timezone.now().strftime('%Y-%m-%dT%H:%M')

    def clean_pub_date(self):
        pub_date = self.cleaned_data.get('pub_date')
        if not pub_date:
            raise forms.ValidationError("Дата публикации обязательна")
        return pub_date

class CommentsForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Оставьте ваш комментарий...'
            }),
        }
