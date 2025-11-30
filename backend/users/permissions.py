from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from users.models import User
from products.models import Product, Category
from orders.models import Order, OrderItem
from reviews.models import Review
from payments.models import Payment
from invoices.models import Invoice

class RolePermissions:
    """Manage role-based permissions following course patterns"""
    
    @classmethod
    def setup_roles_and_permissions(cls):
        """Create all roles and assign permissions"""
        with transaction.atomic():
            cls._create_customer_role()
            cls._create_vendor_role()
            cls._create_admin_role()
    
    @classmethod
    def _create_customer_role(cls):
        """Create Customer role with specific permissions"""
        customer_group, created = Group.objects.get_or_create(name='Customers')
        
        # Permissions for customers
        customer_permissions = [
            # Product permissions
            ('view_product', Product),
            ('view_category', Category),
            
            # Order permissions
            ('view_order', Order),
            ('add_order', Order),
            ('change_order', Order),  # For cart updates
            ('delete_order', Order),  # For cancelling orders
            
            # Review permissions
            ('view_review', Review),
            ('add_review', Review),
            ('change_review', Review),  # Edit own reviews
            ('delete_review', Review),  # Delete own reviews
            
            # Payment permissions
            ('view_payment', Payment),
            ('add_payment', Payment),
            
            # Invoice permissions
            ('view_invoice', Invoice),
        ]
        
        cls._assign_permissions_to_group(customer_group, customer_permissions)
        return customer_group
    
    @classmethod
    def _create_vendor_role(cls):
        """Create Vendor role with specific permissions"""
        vendor_group, created = Group.objects.get_or_create(name='Vendors')
        
        # Permissions for vendors
        vendor_permissions = [
            # Product permissions (full CRUD for own products)
            ('add_product', Product),
            ('change_product', Product),
            ('delete_product', Product),
            ('view_product', Product),
            
            # Category permissions
            ('view_category', Category),
            
            # Order permissions (view and update status for their products)
            ('view_order', Order),
            ('change_order', Order),  # For updating order status
            
            # Shop permissions (manage their own shop)
            ('view_shop', 'users.Shop'),
            ('change_shop', 'users.Shop'),
            
            # Review permissions (view only)
            ('view_review', Review),
        ]
        
        cls._assign_permissions_to_group(vendor_group, vendor_permissions)
        return vendor_group
    
    @classmethod
    def _create_admin_role(cls):
        """Create Admin role with all permissions"""
        admin_group, created = Group.objects.get_or_create(name='Administrators')
        
        # Admins get all permissions
        all_permissions = Permission.objects.all()
        admin_group.permissions.set(all_permissions)
        
        return admin_group
    
    @classmethod
    def _assign_permissions_to_group(cls, group, permission_list):
        """Assign list of permissions to a group"""
        for perm_codename, model in permission_list:
            try:
                if isinstance(model, str):
                    # Handle string format like 'users.Shop'
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
        """Get permissions for a specific role"""
        try:
            group = Group.objects.get(name=role_name)
            return group.permissions.all()
        except Group.DoesNotExist:
            return []
    
    @classmethod
    def user_has_permission(cls, user, perm_codename, model=None):
        """Check if user has specific permission"""
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


# Custom permission checkers following course patterns
def can_create_product(user):
    """Check if user can create products (vendors only)"""
    return user.is_authenticated and user.role == 'vendor'

def can_edit_product(user, product):
    """Check if user can edit a specific product"""
    if not user.is_authenticated:
        return False
    if user.role == 'admin':
        return True
    if user.role == 'vendor':
        return product.shop.user == user
    return False

def can_delete_product(user, product):
    """Check if user can delete a specific product"""
    if not user.is_authenticated:
        return False
    if user.role == 'admin':
        return True
    if user.role == 'vendor':
        # Vendors can only delete their own products without orders
        return (product.shop.user == user and 
                not product.orderitem_set.exists())
    return False

def can_view_order(user, order):
    """Check if user can view a specific order"""
    if not user.is_authenticated:
        return False
    if user.role == 'admin':
        return True
    if user.role == 'vendor':
        # Vendors can see orders containing their products
        return order.orderitem_set.filter(
            product__shop__user=user
        ).exists()
    if user.role == 'customer':
        return order.user == user
    return False

def can_update_order_status(user, order):
    """Check if user can update order status"""
    if not user.is_authenticated:
        return False
    if user.role == 'admin':
        return True
    if user.role == 'vendor':
        # Vendors can update status for orders with their products
        return (order.orderitem_set.filter(
            product__shop__user=user
        ).exists() and 
        order.status in ['paid', 'shipped'])
    return False

def can_cancel_order(user, order):
    """Check if user can cancel an order"""
    if not user.is_authenticated:
        return False
    if user.role == 'admin':
        return True
    if user.role == 'customer':
        # Customers can only cancel their own pending orders
        return (order.user == user and 
                order.status in ['cart', 'pending'])
    return False

def can_create_review(user, product):
    """Check if user can create a review for a product"""
    if not user.is_authenticated or user.role != 'customer':
        return False
    
    # Check if user has purchased the product
    has_purchased = OrderItem.objects.filter(
        order__user=user,
        order__status__in=['paid', 'shipped', 'delivered'],
        product=product
    ).exists()
    
    # Check if user already reviewed
    already_reviewed = Review.objects.filter(
        user=user,
        product=product
    ).exists()
    
    return has_purchased and not already_reviewed

def can_delete_review(user, review):
    """Check if user can delete a review"""
    if not user.is_authenticated:
        return False
    if user.role == 'admin':
        return True
    return review.user == user