from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from datetime import datetime

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    card_type = forms.ChoiceField(
        choices=[
            ('credit_card', 'Carte de Crédit'),
            ('debit_card', 'Carte de Débit'),
            ('paypal', 'PayPal'),
            ('bank_transfer', 'Virement Bancaire')
        ],
        required=True,
        label="Type de paiement"
    )
    card_number = forms.CharField(max_length=16, min_length=16, required=True, help_text="16 digits")
    card_holder = forms.CharField(max_length=100, required=True)
    expiry_month = forms.IntegerField(min_value=1, max_value=12, required=True)
    expiry_year = forms.IntegerField(min_value=datetime.now().year, max_value=datetime.now().year + 10, required=True)
    cvv = forms.CharField(max_length=3, min_length=3, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def clean_card_number(self):
        number = self.cleaned_data.get('card_number')
        if not number.isdigit():
            raise forms.ValidationError("Card number must be digits only.")
        return number

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)