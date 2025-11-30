from django import forms
from .models import Product, Category

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock_quantity', 'category']
        labels = {
            'name': 'Nom du produit',
            'description': 'Description',
            'price': 'Prix',
            'stock_quantity': 'Quantité en stock',
            'category': 'Catégorie'
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'parent']