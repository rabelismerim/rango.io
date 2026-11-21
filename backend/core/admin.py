from django.contrib import admin
from .models import Restaurant, Product, Option, Order, OrderItem
for model in [Restaurant, Product, Option, Order, OrderItem]: admin.site.register(model)
