from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Shop

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role']

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)

class ShopForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ['name', 'description']
        labels = {
            'name': 'Nom du magasin',
            'description': 'Description'
        }