from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import Restaurant, Product

class Command(BaseCommand):
    help = 'Cria usuários e cardápio de demonstração. Apenas desenvolvimento.'
    def handle(self, **options):
        from django.conf import settings
        if not settings.DEBUG: raise RuntimeError('Seed permitido apenas em DEBUG.')
        User = get_user_model()
        for username in ['cliente', 'lojista']:
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_password('RangoDemo2026!')
                user.save()
        owner = User.objects.get(username='lojista')
        names = [('Burguer & Brasa','Hambúrgueres'),('Basilico Pizza','Pizzas'),('Nori Sushi','Japonesa'),('Verde & Grão','Saudável'),('Pasta & Basta','Massas'),('Doce Encontro','Doces')]
        for pk, (name, category) in enumerate(names, 1): Restaurant.objects.update_or_create(pk=pk, defaults={'owner':owner,'name':name,'category':category})
        products = [(1,1,'Brasa da casa','32.90'),(2,1,'Duplo smash','36.90'),(3,2,'Margherita artesanal','49.90'),(4,2,'Pepperoni','56.90'),(5,3,'Combinado Nori · 24 peças','79.90'),(6,4,'Bowl da estação','29.90'),(7,5,'Pesto da nonna','42.90'),(8,6,'Fatia de chocolate','19.90')]
        for pk, restaurant, name, price in products: Product.objects.update_or_create(pk=pk, defaults={'restaurant_id':restaurant,'name':name,'price':price})
        self.stdout.write(self.style.SUCCESS('Demo: cliente / lojista — senha RangoDemo2026!'))
