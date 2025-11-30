from django.db import models
from django.contrib.auth.models import AbstractUser
from .permissions import can_create_product, can_edit_product, can_delete_product

class User(AbstractUser):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
        ('admin', 'Administrator'),
    ]
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
    def is_vendor(self):
        return self.role == 'vendor'
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_customer(self):
        return self.role == 'customer'
    
    # Permission shortcut methods
    def can_create_products(self):
        return can_create_product(self)
    
    def can_edit_product(self, product):
        return can_edit_product(self, product)
    
    def can_delete_product(self, product):
        return can_delete_product(self, product)
    
    def get_shop(self):
        """Get user's shop if they are a vendor"""
        if self.is_vendor():
            return self.shop_set.first()
        return None

class Shop(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'vendor'})
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    def __str__(self):
        return self.name