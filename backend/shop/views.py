from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Shop
from .serializers import ShopSerializer

class ShopModelViewSet(viewsets.ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
