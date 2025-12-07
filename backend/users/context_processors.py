from django.contrib.auth.context_processors import auth

def user_permissions(request):
    context = {}
    if hasattr(request, 'user') and request.user.is_authenticated:
        context['user_can_create_products'] = request.user.has_perm('products.add_product')
        context['user_can_edit_products'] = request.user.has_perm('products.change_product')
        context['user_can_delete_products'] = request.user.has_perm('products.delete_product')
        context['user_can_view_orders'] = request.user.has_perm('orders.view_order')
        context['user_can_edit_orders'] = request.user.has_perm('orders.change_order')
        context['user_can_delete_orders'] = request.user.has_perm('orders.delete_order')
        
        context['user_is_vendor'] = request.user.role == 'vendor'
        context['user_is_admin'] = request.user.role == 'admin'
        context['user_is_customer'] = request.user.role == 'customer'
        
        if request.user.role == 'vendor':
            from shop.models import Shop
            context['user_shop'] = Shop.objects.filter(user=request.user).first()
    
    return context