from django.db import models
from orders.models import Order

class Invoice(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=50, unique=True)
    issue_date = models.DateField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Invoice {self.invoice_number}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last_invoice = Invoice.objects.order_by('-id').first()
            last_number = int(last_invoice.invoice_number.split('-')[-1]) if last_invoice else 0
            self.invoice_number = f"INV-{last_number + 1:06d}"
        super().save(*args, **kwargs)