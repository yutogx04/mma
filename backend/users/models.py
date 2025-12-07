from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin


class CompteManager(BaseUserManager):
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(email, password, **extra_fields)


class Compte(AbstractUser):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
        ('admin', 'Administrator'),
    ]
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = CompteManager()
    
    REQUIRED_FIELDS = ['email', 'role']
    
    def __str__(self):
        return f"{self.username} ({self.role})"
    
    def is_vendor(self):
        return self.role == 'vendor'
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_customer(self):
        return self.role == 'customer'
    
    def can_create_products(self):
        from .permissions import can_create_product
        return can_create_product(self)
    
    def can_edit_product(self, product):
        from .permissions import can_edit_product
        return can_edit_product(self, product)
    
    def can_delete_product(self, product):
        from .permissions import can_delete_product
        return can_delete_product(self, product)
    
    def get_shop(self):
        if self.is_vendor():
            return self.shop_set.first()
        return None


User = Compte