from django.contrib import messages 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse, HttpResponseForbidden
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count
from django.views.decorators.http import require_http_methods


from .models import Product, Category
from .forms import ProductForm
from users.decorators import vendor_required
from users.permissions import can_edit_product, can_delete_product, can_create_product
from shop.models import Shop
from orders.models import Order, OrderItem
from .serializers import ProductSerializer, CategorySerializer

# Constants
PERMISSION_DENIED = "Permission denied"


@require_http_methods(["GET"])
def product_list(request):
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    
    products = Product.objects.select_related('shop', 'category').all()
    categories = Category.objects.all()
    
    if search_query:
        products = products.filter(name__icontains=search_query)
    if category_id:
        products = products.filter(category_id=category_id)
    
    return render(request, "products/list.html", {
        'products': products,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
    })

@require_http_methods(["GET", "POST"])

@login_required
def create_product_view(request):
    if not (request.user.role == 'vendor' or request.user.role == 'admin'):
        return HttpResponseForbidden(PERMISSION_DENIED)
    
    categories = Category.objects.all()
    
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            
            if request.user.role == 'vendor':
                shop = request.user.shop_set.first()
                if shop:
                    product.shop = shop
                    product.save()
                    messages.success(request, "Produit créé avec succès!")
                    return redirect('product_list')
                else:
                    form.add_error(None, 'Vous devez créer un magasin avant d\'ajouter des produits')
            elif request.user.role == 'admin':
                product.save()
                messages.success(request, "Produit créé avec succès!")
                return redirect('product_list')
    else:
        form = ProductForm()
    
    return render(request, "products/create.html", {
        'form': form,
        'categories': categories
    })


@require_http_methods(["GET", "POST"])
@login_required
def update_product_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if not (request.user.role == 'admin' or (request.user.role == 'vendor' and product.shop.user == request.user)):
        return HttpResponseForbidden(PERMISSION_DENIED)
    
    categories = Category.objects.all()
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Produit modifié avec succès!")
            return redirect('product_detail', product_id=product.id)
    else:
        form = ProductForm(instance=product)

    return render(request, "products/update.html", {
        'form': form,
        'product': product,
        'categories': categories 
    })


@require_http_methods(["GET", "POST", "DELETE"])
@login_required
def delete_product_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if not (request.user.role == 'admin' or (request.user.role == 'vendor' and product.shop.user == request.user)):
        return HttpResponseForbidden(PERMISSION_DENIED)
    
    if request.method in ['POST', 'DELETE']:
        if product.orderitem_set.exists():
            messages.error(request, "Impossible de supprimer un produit avec des commandes associées")
            return redirect('product_detail', product_id=product.id)
        
        product_name = product.name
        product.delete()
        messages.success(request, f'Produit "{product_name}" supprimé avec succès')
        return redirect('product_list')
    
    return render(request, "products/delete_confirm.html", {
        'product': product
    })

@require_http_methods(["GET", "POST"])
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        
        quantity = int(request.POST.get("quantity", 1))
        
        cart, created = Order.objects.get_or_create(
            user=request.user,
            status='cart',
            defaults={'total_amount': 0}
        )
        
        order_item, created = OrderItem.objects.get_or_create(
            order=cart,
            product=product,
            defaults={'quantity': quantity, 'price': product.price}
        )
        
        if not created:
            order_item.quantity += quantity
            order_item.save()
        
        messages.success(request, "Produit ajouté au panier!")
        return redirect('product_detail', product_id=product.id)

    return render(request, "products/detail.html", {
        'product': product
    })

@require_http_methods(["GET"])
@login_required
def vendor_products_view(request):
    if request.user.role != 'vendor':
        return HttpResponseForbidden("Access réservé aux vendeurs")
    
    shop = get_object_or_404(Shop, user=request.user)
    
    products = Product.objects.filter(shop=shop).select_related('category').annotate(
        order_count=Count('orderitem')
    ).order_by('-created_at')
    
    low_stock_count = products.filter(stock_quantity__lt=10, stock_quantity__gt=0).count()
    out_of_stock_count = products.filter(stock_quantity=0).count()
    
    context = {
        'products': products,
        'shop': shop,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
    }
    
    return render(request, "products/vendor_products.html", context)

@require_http_methods(["POST"])
def add_to_cart_view(request):
    product_id = request.POST.get("product_id")
    quantity = int(request.POST.get("quantity", 1))
    
    if not product_id:
        messages.error(request, "Produit non spécifié")
        return redirect('product_list')
    
    product = get_object_or_404(Product, id=product_id)
    

    if quantity > product.stock_quantity:
        messages.error(request, f"Stock insuffisant. Quantité disponible: {product.stock_quantity}")
        return redirect('product_detail', product_id=product_id)
    
    cart, _ = Order.objects.get_or_create(
        user=request.user,
        status='cart',
        defaults={'total_amount': 0}
    )
    
    order_item, item_created = OrderItem.objects.get_or_create(
        order=cart,
        product=product,
        defaults={'quantity': quantity, 'price': product.price}
    )
    
    if not item_created:
        order_item.quantity += quantity
        order_item.save()
    
    cart.total_amount = sum(
        item.quantity * item.price for item in cart.orderitem_set.all()
    )
    cart.save()
    
    messages.success(request, f"✅ {product.name} ajouté au panier!")
    
    redirect_to = request.POST.get('redirect_to', 'cart_view')
    if redirect_to == 'product_detail':
        return redirect('product_detail', product_id=product_id)
    return redirect('cart_view')


from rest_framework.authentication import SessionAuthentication

class ProductModelViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]
    
    def perform_create(self, serializer):
        if self.request.user.role == 'vendor':
            shop = self.request.user.shop_set.first()
            serializer.save(shop=shop)
        else:
            serializer.save()

class CategoryModelViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication]