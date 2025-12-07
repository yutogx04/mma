from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Invoice
from orders.models import Order
from rest_framework import status

@login_required
def invoice_detail_view(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, order__user=request.user)
    
    return render(request, "invoices/detail.html", {
        'invoice': invoice
    })

@api_view(['POST'])
@login_required
def invoice_create_api(request):
    order_id = request.data.get('order_id')
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if Invoice.objects.filter(order=order).exists():
        return Response(
            {'error': 'Invoice already exists for this order'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    invoice = Invoice.objects.create(
        order=order,
        amount=order.total_amount
    )
    
    return Response({
        'id': invoice.id,
        'invoice_number': invoice.invoice_number,
        'amount': str(invoice.amount),
        'message': 'Invoice created successfully'
    })

@api_view(['GET'])
@login_required
def invoice_detail_api(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, order__user=request.user)
    
    data = {
        'id': invoice.id,
        'invoice_number': invoice.invoice_number,
        'order_id': invoice.order.id,
        'amount': str(invoice.amount),
        'issue_date': invoice.issue_date,
        'created_at': invoice.created_at
    }
    
    return Response(data)