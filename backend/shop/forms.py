from django import forms
from .models import Shop


class ShopForm(forms.ModelForm):
    """Form for creating and updating shops"""
    class Meta:
        model = Shop
        fields = ['name', 'description']
        labels = {
            'name': 'Nom du magasin',
            'description': 'Description'
        }
