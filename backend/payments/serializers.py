from rest_framework import serializers
from .models import Payment, PaymentMethod

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'card_type', 'card_last_four', 'card_holder_name', 'expiry_month', 'expiry_year', 'is_default']
        read_only_fields = ['card_last_four', 'payment_token'] # Don't allow writing these directly via API updates

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
