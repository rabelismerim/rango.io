from django.conf import settings
from django.db import models

class Restaurant(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=80)
    latitude = models.FloatField(default=-23.5505)
    longitude = models.FloatField(default=-46.6333)
    delivery_base = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    delivery_per_km = models.DecimalField(max_digits=8, decimal_places=2, default=2)
    max_distance_km = models.PositiveIntegerField(default=20)
    is_open = models.BooleanField(default=True)
    def __str__(self): return self.name

class Product(models.Model):
    restaurant = models.ForeignKey(Restaurant, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=80, default='Principais')
    price = models.DecimalField(max_digits=8, decimal_places=2)
    available = models.BooleanField(default=True)

class Option(models.Model):
    product = models.ForeignKey(Product, related_name='options', on_delete=models.CASCADE)
    name = models.CharField(max_length=80)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    available = models.BooleanField(default=True)

class Order(models.Model):
    STATUSES = [('pending', 'Pendente'), ('preparing', 'Em preparo'), ('out_for_delivery', 'Saiu para entrega'), ('delivered', 'Entregue')]
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.PROTECT)
    address = models.CharField(max_length=300)
    status = models.CharField(max_length=24, choices=STATUSES, default='pending')
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at', '-id']

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    name = models.CharField(max_length=120)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    options_snapshot = models.JSONField(default=list)
