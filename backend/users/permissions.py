from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction



class RolePermissions:
    
    @classmethod
    def setup_roles_and_permissions(cls):
        from users.models import User  
        from products.models import Product, Category
        from orders.models import Order, OrderItem
        from reviews.models import Review
        from payments.models import Payment
        from invoices.models import Invoice
        
        with transaction.atomic():
            cls._create_customer_role()
            cls._create_vendor_role()
            cls._create_admin_role()
    
    @classmethod
    def _create_customer_role(cls):
        from products.models import Product, Category
        from orders.models import Order
        from reviews.models import Review
        from payments.models import Payment
        from invoices.models import Invoice
        
        customer_group, created = Group.objects.get_or_create(name='Customers')
        
        customer_permissions = [
            ('view_product', Product),
            ('view_category', Category),
            
            ('view_order', Order),
            ('add_order', Order),
            ('change_order', Order), 
            ('delete_order', Order),  
            
            ('view_review', Review),
            ('add_review', Review),
            ('change_review', Review),  
            ('delete_review', Review),  
            
            ('view_payment', Payment),
            ('add_payment', Payment),
            
            ('view_invoice', Invoice),
        ]
        
        cls._assign_permissions_to_group(customer_group, customer_permissions)
        return customer_group
    
    @classmethod
    def _create_vendor_role(cls):
        from products.models import Product, Category
        from orders.models import Order
        from reviews.models import Review
        
        vendor_group, created = Group.objects.get_or_create(name='Vendors')
        
        vendor_permissions = [
            ('add_product', Product),
            ('change_product', Product),
            ('delete_product', Product),
            ('view_product', Product),
            
            ('view_category', Category),
            
            ('view_order', Order),
            ('change_order', Order),
            
            ('view_shop', 'shop.Shop'),
            ('change_shop', 'shop.Shop'),
            
            ('view_review', Review),
        ]
        
        cls._assign_permissions_to_group(vendor_group, vendor_permissions)
        return vendor_group
    
    @classmethod
    def _create_admin_role(cls):
        admin_group, created = Group.objects.get_or_create(name='Administrators')
        all_permissions = Permission.objects.all()
        admin_group.permissions.set(all_permissions)
        return admin_group
    
    @classmethod
    def _assign_permissions_to_group(cls, group, permission_list):
        for perm_codename, model in permission_list:
            try:
                if isinstance(model, str):
                    app_label, model_name = model.split('.')
                    content_type = ContentType.objects.get(
                        app_label=app_label, 
                        model=model_name.lower()
                    )
                else:
                    content_type = ContentType.objects.get_for_model(model)
                
                permission = Permission.objects.get(
                    codename=perm_codename,
                    content_type=content_type
                )
                group.permissions.add(permission)
            except (ContentType.DoesNotExist, Permission.DoesNotExist):
                print(f"Warning: Permission {perm_codename} for {model} not found")
                continue
    
    @classmethod
    def get_role_permissions(cls, role_name):
        try:
            group = Group.objects.get(name=role_name)
            return group.permissions.all()
        except Group.DoesNotExist:
            return []
    
    @classmethod
    def user_has_permission(cls, user, perm_codename, model=None):
        if user.is_superuser:
            return True
        
        if model:
            if isinstance(model, str):
                app_label, model_name = model.split('.')
                content_type = ContentType.objects.get(
                    app_label=app_label, 
                    model=model_name.lower()
                )
            else:
                content_type = ContentType.objects.get_for_model(model)
            
            perm_name = f"{content_type.app_label}.{perm_codename}"
            return user.has_perm(perm_name)
        
        return user.has_perm(perm_codename)


def can_create_product(user):
    from users.models import User
    return user.is_authenticated and user.role == 'vendor'

def can_edit_product(user, product):
    if not user.is_authenticated:
        return False
    if user.role == 'admin':
        return True
    if user.role == 'vendor':
        return product.shop.user == user
    return False

def can_delete_product(user, product):
    if not user.is_authenticated:
        return False
    
    if not hasattr(user, 'role'):
        return False
    
    if user.role == 'admin':
        return True
    
    if user.role == 'vendor':
        if hasattr(product, 'shop') and product.shop and hasattr(product.shop, 'user'):
            return product.shop.user == user
        return False
    
    return False

def can_view_order(user, order):
    if not user.is_authenticated:
        return False
    if user.role == 'admin':
        return True
    if user.role == 'vendor':
        return order.orderitem_set.filter(
            product__shop__user=user
        ).exists()
    if user.role == 'customer':
        return order.user == user
    return False

def can_update_order_status(user, order):
    if not user.is_authenticated:
        return False
    if user.role == 'admin':
        return True
    if user.role == 'vendor':
        return (order.orderitem_set.filter(
            product__shop__user=user
        ).exists() and 
        order.status in ['paid', 'shipped'])
    return False

def can_cancel_order(user, order):
    if not user.is_authenticated:
        return False
    if user.role == 'admin':
        return True
    if user.role == 'customer':
        return (order.user == user and 
                order.status in ['cart', 'pending'])
    return False

def can_create_review(user, product):
    if not user.is_authenticated or user.role != 'customer':
        return False
    
    from orders.models import OrderItem
    from reviews.models import Review
    
    has_purchased = OrderItem.objects.filter(
        order__user=user,
        order__status__in=['paid', 'shipped', 'delivered'],
        product=product
    ).exists()
    
    already_reviewed = Review.objects.filter(
        user=user,
        product=product
    ).exists()
    
    return has_purchased and not already_reviewed

def can_delete_review(user, review):
    if not user.is_authenticated:
        return False
    if user.role == 'admin':
        return True
    return review.user == user