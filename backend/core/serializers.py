from decimal import Decimal
from math import radians, sin, cos, atan2, sqrt
from django.db import transaction
from rest_framework import serializers
from .models import Restaurant, Product, Option, Order, OrderItem

class OptionSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=Decimal('0'))
    class Meta:
        model = Option
        fields = ['id', 'name', 'price', 'available', 'product']

class ProductSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=Decimal('0.01'))
    options = OptionSerializer(many=True, read_only=True)
    class Meta:
        model = Product
        fields = ['id', 'restaurant', 'name', 'description', 'category', 'price', 'available', 'options']

class RestaurantSerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)
    class Meta:
        model = Restaurant
        exclude = ['owner']

class LineInput(serializers.Serializer):
    product = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, max_value=99)
    options = serializers.ListField(child=serializers.IntegerField(), default=list)

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        exclude = ['order']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    class Meta:
        model = Order
        exclude = ['customer']
        read_only_fields = ['status', 'delivery_fee', 'total', 'created_at']

class CheckoutSerializer(serializers.Serializer):
    restaurant = serializers.PrimaryKeyRelatedField(queryset=Restaurant.objects.all())
    address = serializers.CharField(max_length=300)
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)
    items = LineInput(many=True, allow_empty=False)

    @transaction.atomic
    def create(self, data):
        r = Restaurant.objects.select_for_update().get(pk=data['restaurant'].pk)
        if not r.is_open: raise serializers.ValidationError('Restaurante fechado.')
        lat1, lat2 = radians(r.latitude), radians(data['latitude'])
        dlat, dlon = lat2-lat1, radians(data['longitude']-r.longitude)
        a = min(1, max(0, sin(dlat/2)**2+cos(lat1)*cos(lat2)*sin(dlon/2)**2))
        distance = 6371*2*atan2(sqrt(a), sqrt(1-a))
        if distance > r.max_distance_km: raise serializers.ValidationError('Endereço fora da área de entrega.')
        fee = (r.delivery_base + r.delivery_per_km * Decimal(str(distance))).quantize(Decimal('.01'))
        lines, subtotal = [], Decimal(0)
        for line in data['items']:
            try: p = Product.objects.select_for_update().get(pk=line['product'], restaurant=r, available=True)
            except Product.DoesNotExist: raise serializers.ValidationError('Produto indisponível ou de outro restaurante.')
            ids = line['options']
            options = list(Option.objects.select_for_update().filter(pk__in=ids, product=p, available=True))
            if len(options) != len(ids): raise serializers.ValidationError('Adicionais inválidos.')
            price = p.price + sum((o.price for o in options), Decimal(0))
            subtotal += price * line['quantity']
            lines.append(dict(product=p, name=p.name, quantity=line['quantity'], unit_price=price, options_snapshot=[{'id':o.pk, 'name':o.name, 'price':str(o.price)} for o in options]))
        order = Order.objects.create(customer=self.context['request'].user, restaurant=r, address=data['address'], delivery_fee=fee, total=subtotal+fee)
        OrderItem.objects.bulk_create([OrderItem(order=order, **line) for line in lines])
        from .tasks import notify_order
        transaction.on_commit(lambda: notify_order.delay(order.pk))
        return order
