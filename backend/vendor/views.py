
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from orders.models import VendorOrder, VendorPayout
from decimal import Decimal

VENDOR_ACCESS_DENIED = "Accès réservé aux vendeurs"

@login_required
def vendor_orders_list(request):
    if request.user.role != 'vendor':
        messages.error(request, VENDOR_ACCESS_DENIED)
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
    if not _check_vendor_permission(request):
        return redirect('dashboard')
    
    vendor_order = _get_vendor_order(vendor_order_id, request.user)
    
    if request.method == 'POST':
        _handle_post_actions(request, vendor_order)
        return redirect('vendor_order_detail', vendor_order_id=vendor_order.id)
    
    return _render_order_detail(vendor_order)

def _check_vendor_permission(request):
    """Check if user has vendor permissions"""
    if request.user.role != 'vendor':
        messages.error(request, VENDOR_ACCESS_DENIED)
        return False
    return True

def _get_vendor_order(vendor_order_id, user):
    """Get vendor order with proper permissions"""
    return get_object_or_404(
        VendorOrder,
        id=vendor_order_id,
        vendor=user
    )

def _handle_post_actions(request, vendor_order):
    """Handle POST actions for vendor order"""
    action = request.POST.get('action')
    
    if action == 'mark_shipped':
        _handle_mark_shipped(request, vendor_order)
    elif action == 'mark_delivered':
        _handle_mark_delivered(request, vendor_order)
    elif action == 'cancel':
        _handle_cancel_order(request, vendor_order)


def _handle_mark_shipped(request, vendor_order):
    """Handle marking order as shipped"""
    tracking = request.POST.get('tracking_number', '')
    if not tracking:
        messages.error(request, "Numéro de suivi requis")
        return
    
    vendor_order.status = 'shipped'
    vendor_order.tracking_number = tracking
    vendor_order.shipped_at = timezone.now()
    vendor_order.save()
    
    vendor_order.orderitem_set.update(status='shipped')
    
    _create_shipment_notification(vendor_order, tracking)
    messages.success(request, "Commande marquée comme expédiée!")

def _handle_mark_delivered(request, vendor_order):
    """Handle marking order as delivered"""
    vendor_order.status = 'delivered'
    vendor_order.delivered_at = timezone.now()
    vendor_order.save()
    
    vendor_order.orderitem_set.update(status='delivered')
    
    _create_vendor_payout(vendor_order)
    _create_delivery_notification(vendor_order)
    messages.success(request, "Commande marquée comme livrée! Paiement en attente.")

def _handle_cancel_order(request, vendor_order):
    """Handle cancelling an order"""
    if vendor_order.status not in ['pending', 'processing']:
        messages.error(request, "Impossible d'annuler une commande déjà expédiée.")
        return
    
    vendor_order.status = 'cancelled'
    vendor_order.save()
    
    _restore_product_stock(vendor_order)
    messages.success(request, "Commande annulée et stock restauré.")


def _create_shipment_notification(vendor_order, tracking):
    """Create notification for order shipment"""
    try:
        from notifications.models import Notification
        Notification.objects.create(
            user=vendor_order.order.user,
            type='order_shipped',
            message="Votre commande (vendeur: {}) a été expédiée! Suivi: {}".format(
                vendor_order.vendor.username, tracking),
            related_id=vendor_order.order.id
        )
    except Exception:
        pass


def _create_delivery_notification(vendor_order):
    """Create notification for order delivery"""
    try:
        from notifications.models import Notification
        Notification.objects.create(
            user=vendor_order.order.user,
            type='order_delivered',
            message="Votre commande (vendeur: {}) a été livrée!".format(
                vendor_order.vendor.username),
            related_id=vendor_order.order.id
        )
    except Exception:
        pass

def _create_vendor_payout(vendor_order):
    """Create vendor payout record"""
    VendorPayout.objects.create(
        vendor=vendor_order.vendor,
        vendor_order=vendor_order,
        amount=vendor_order.vendor_payout,
        status='pending'
    )

def _restore_product_stock(vendor_order):
    """Restore product stock for cancelled order"""
    for item in vendor_order.orderitem_set.all():
        item.product.stock_quantity += item.quantity
        item.product.save()
        item.status = 'cancelled'
        item.save()

def _render_order_detail( request ,vendor_order):
    """Render vendor order detail page"""
    return render(request, 'vendor/order_detail.html', {
        'vendor_order': vendor_order
    })


@login_required
def vendor_earnings(request):
    if request.user.role != 'vendor':
        messages.error(request, VENDOR_ACCESS_DENIED)
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
