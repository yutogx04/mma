
from django.contrib.auth.decorators import user_passes_test
from functools import wraps
from .permissions import can_create_product, can_edit_product, can_delete_product

# Constants
LOGIN_URL = '/api/auth/login/'


def vendor_required(function=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.role == 'vendor',
        login_url=LOGIN_URL
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def admin_required(function=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.role == 'admin',
        login_url=LOGIN_URL
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def customer_required(function=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.role == 'customer',
        login_url=LOGIN_URL
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def can_create_product_required(function=None):
    actual_decorator = user_passes_test(
        lambda u: can_create_product(u),
        login_url=LOGIN_URL
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def can_manage_shop_required(function=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.role in ['vendor', 'admin'],
        login_url=LOGIN_URL
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
