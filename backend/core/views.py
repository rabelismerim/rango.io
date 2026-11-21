from django.db import transaction
from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import Restaurant, Product, Option, Order
from .serializers import RestaurantSerializer, ProductSerializer, OptionSerializer, OrderSerializer, CheckoutSerializer
from .tasks import notify_order

class RestaurantViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = Restaurant.objects.prefetch_related('products__options').filter(is_open=True)
    serializer_class = RestaurantSerializer

class MerchantMixin:
    def get_queryset(self): return super().get_queryset().filter(restaurant__owner=self.request.user)
    def perform_create(self, serializer):
        r = serializer.validated_data.get('restaurant')
        if r is None:
            product = serializer.validated_data.get('product')
            if product is not None: r = product.restaurant
            elif isinstance(serializer.instance, Product): r = serializer.instance.restaurant
            else: r = serializer.instance.product.restaurant
        if r.owner_id != self.request.user.pk: raise PermissionDenied()
        serializer.save()
    def perform_update(self, serializer): self.perform_create(serializer)

class ProductViewSet(MerchantMixin, viewsets.ModelViewSet):
    queryset = Product.objects.prefetch_related('options')
    serializer_class = ProductSerializer

class OptionViewSet(MerchantMixin, viewsets.ModelViewSet):
    queryset = Option.objects.select_related('product__restaurant')
    serializer_class = OptionSerializer
    def get_queryset(self): return Option.objects.filter(product__restaurant__owner=self.request.user)

class StatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.STATUSES)

class OrderViewSet(viewsets.ModelViewSet):
    http_method_names = ['get', 'post', 'head', 'options']
    queryset = Order.objects.select_related('restaurant').prefetch_related('items')
    serializer_class = OrderSerializer
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(restaurant__owner=self.request.user) if self.request.query_params.get('merchant') == '1' else qs.filter(customer=self.request.user)
    def get_serializer_class(self): return CheckoutSerializer if self.action == 'create' else StatusSerializer if self.action == 'status' else OrderSerializer
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(OrderSerializer(serializer.save()).data, status=201)
    @action(detail=True, methods=['post'])
    def status(self, request, pk=None):
        with transaction.atomic():
            order = Order.objects.select_for_update().filter(pk=pk, restaurant__owner=request.user).first()
            if not order: raise PermissionDenied()
            serializer = StatusSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            states = [s[0] for s in Order.STATUSES]
            if order.status == states[-1] or serializer.validated_data['status'] != states[states.index(order.status)+1]:
                raise ValidationError('Transição de status inválida.')
            order.status = serializer.validated_data['status']
            order.save(update_fields=['status'])
            transaction.on_commit(lambda: notify_order.delay(order.pk))
        return Response(OrderSerializer(order).data)
