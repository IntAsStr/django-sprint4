from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm
from .models import Post, Comments

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
            'pub_date': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            )
        }


class CommentsForm(forms.ModelForm):
    class Meta:
        model = Comments
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Оставьте ваш комментарий...'
            }),
        }
