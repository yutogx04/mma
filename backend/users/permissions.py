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