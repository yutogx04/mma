from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from orders.models import VendorOrder, VendorPayout
from decimal import Decimal

@login_required
def vendor_orders_list(request):
    if request.user.role != 'vendor':
        messages.error(request, "Accès réservé aux vendeurs")
        return redirect('dashboard')
    
    vendor_orders = VendorOrder.objects.filter(
        vendor=request.user
    ).select_related('order__user').prefetch_related('orderitem_set__product').order_by('-created_at')
    
    total_sales = sum(vo.vendor_total for vo in vendor_orders)
    total_commission = sum(vo.platform_fee for vo in vendor_orders)
    total_payout = sum(vo.vendor_payout for vo in vendor_orders)
    pending_count = vendor_orders.filter(status='pending').count()
    
    context = {
'vendor_orders': vendor_orders,
        'stats': {
            'total_sales': total_sales,
            'total_commission': total_commission,
            'total_payout': total_payout,
            'pending_count': pending_count,
        }
    }
    
    return render(request, 'vendor/orders_list.html', context)

@login_required
def vendor_order_detail(request, vendor_order_id):
    if request.user.role != 'vendor':
        messages.error(request, "Accès réservé aux vendeurs")
        return redirect('dashboard')
    
    vendor_order = get_object_or_404(
        VendorOrder,
        id=vendor_order_id,
        vendor=request.user
    )
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'mark_shipped':
            tracking = request.POST.get('tracking_number', '')
            if not tracking:
                messages.error(request, "Numéro de suivi requis")
                return redirect('vendor_order_detail', vendor_order_id=vendor_order.id)
            
            vendor_order.status = 'shipped'
            vendor_order.tracking_number = tracking
            vendor_order.shipped_at = timezone.now()
            vendor_order.save()
            
            vendor_order.orderitem_set.update(status='shipped')
            
            try:
                from notifications.models import Notification
                Notification.objects.create(
                    user=vendor_order.order.user,
                    type='order_shipped',
                    message=f"Votre commande (vendeur: {vendor_order.vendor.username}) a été expédiée! Suivi: {tracking}",
                    related_id=vendor_order.order.id
                )
            except:
                pass
            
            messages.success(request, "Commande marquée comme expédiée!")
            
        elif action == 'mark_delivered':
            vendor_order.status = 'delivered'
            vendor_order.delivered_at = timezone.now()
            vendor_order.save()
            
            vendor_order.orderitem_set.update(status='delivered')
            

            VendorPayout.objects.create(
                vendor=request.user,
                vendor_order=vendor_order,
                amount=vendor_order.vendor_payout,
                status='pending'
            )
            

            try:
                from notifications.models import Notification
                Notification.objects.create(
                    user=vendor_order.order.user,
                    type='order_delivered',
                    message=f"Votre commande (vendeur: {vendor_order.vendor.username}) a été livrée!",
                    related_id=vendor_order.order.id
                )
            except:
                pass
            
            messages.success(request, "Commande marquée comme livrée! Paiement en attente.")
            
        elif action == 'cancel':
            if vendor_order.status in ['pending', 'processing']:
                vendor_order.status = 'cancelled'
                vendor_order.save()
                
                for item in vendor_order.orderitem_set.all():
                    item.product.stock_quantity += item.quantity
                    item.product.save()
                    item.status = 'cancelled'
                    item.save()
                
                messages.success(request, "Commande annulée et stock restauré.")
            else:
                messages.error(request, "Impossible d'annuler une commande déjà expédiée.")
    
    return render(request, 'vendor/order_detail.html', {
        'vendor_order': vendor_order
    })

@login_required
def vendor_earnings(request):
    if request.user.role != 'vendor':
        messages.error(request, "Accès réservé aux vendeurs")
        return redirect('dashboard')
    
    payouts = VendorPayout.objects.filter(vendor=request.user).order_by('-created_at')
    
    total_earned = sum(p.amount for p in payouts)
    paid_out = sum(p.amount for p in payouts.filter(status='paid'))
    pending_payout = sum(p.amount for p in payouts.filter(status='pending'))
    
    context = {
        'payouts': payouts,
        'stats': {
            'total_earned': total_earned,
            'paid_out': paid_out,
            'pending_payout': pending_payout,
        }
    }
    
    return render(request, 'vendor/earnings.html', context)
