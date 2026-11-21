from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from .models import Restaurant, Product, Option, Order

class CheckoutTests(TestCase):
    def setUp(self):
        self.customer=get_user_model().objects.create_user(username='customer')
        self.owner=get_user_model().objects.create_user(username='owner')
        self.other=get_user_model().objects.create_user(username='other')
        self.r=Restaurant.objects.create(owner=self.owner,name='Brasa',delivery_base=5)
        self.p=Product.objects.create(restaurant=self.r,name='Burger',price=20)
        self.option=Option.objects.create(product=self.p,name='Queijo',price=3)
        self.client=APIClient()
        self.client.force_authenticate(self.customer)
    def payload(self, **kwargs):
        data={'restaurant':self.r.pk,'address':'Rua Augusta, 1500','latitude':self.r.latitude,'longitude':self.r.longitude,'items':[{'product':self.p.pk,'quantity':2,'options':[self.option.pk]}],'total':'0.01'}
        data.update(kwargs)
        return data
    def test_server_calculates_prices_and_options(self):
        response=self.client.post('/api/orders/',self.payload(),format='json')
        self.assertEqual(response.status_code,201,response.data)
        self.assertEqual(Decimal(response.data['total']),Decimal('51'))
        self.assertEqual(response.data['items'][0]['options_snapshot'][0]['name'],'Queijo')
    def test_other_restaurant_rejected_atomically(self):
        r=Restaurant.objects.create(owner=self.other,name='Outro')
        p=Product.objects.create(restaurant=r,name='Pizza',price=50)
        response=self.client.post('/api/orders/',self.payload(items=[{'product':p.pk,'quantity':1}]),format='json')
        self.assertEqual(response.status_code,400)
        self.assertEqual(Order.objects.count(),0)
    def test_closed_and_unavailable_rejected(self):
        self.p.available=False;self.p.save()
        self.assertEqual(self.client.post('/api/orders/',self.payload(),format='json').status_code,400)
        self.r.is_open=False;self.r.save()
        self.assertEqual(self.client.post('/api/orders/',self.payload(),format='json').status_code,400)
    def test_distance_and_negative_quantity(self):
        self.assertEqual(self.client.post('/api/orders/',self.payload(latitude=0),format='json').status_code,400)
        self.assertEqual(self.client.post('/api/orders/',self.payload(items=[{'product':self.p.pk,'quantity':-1}]),format='json').status_code,400)
    def test_permissions_and_status_machine(self):
        created=self.client.post('/api/orders/',self.payload(),format='json').data
        url=f'/api/orders/{created["id"]}/status/'
        self.assertEqual(self.client.post(url,{'status':'preparing'}).status_code,403)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f'/api/orders/{created["id"]}/').status_code,404)
        self.assertEqual(self.client.patch(f'/api/products/{self.p.pk}/',{'available':False}).status_code,404)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.post(url,{'status':'delivered'}).status_code,400)
        for status in ['preparing','out_for_delivery','delivered']:
            self.assertEqual(self.client.post(url,{'status':status}).status_code,200)
        self.assertEqual(self.client.post(url,{'status':'preparing'}).status_code,400)

class RealtimeTests(CheckoutTests):
    def test_notification_after_commit(self):
        from unittest.mock import patch
        with patch('core.tasks.notify_order.delay') as notify:
            with self.captureOnCommitCallbacks(execute=True):
                response=self.client.post('/api/orders/',self.payload(),format='json')
            notify.assert_called_once_with(response.data['id'])

    async def test_socket_permissions_and_event(self):
        from channels.testing import WebsocketCommunicator
        from channels.db import database_sync_to_async
        from channels.layers import get_channel_layer
        from rest_framework_simplejwt.tokens import AccessToken
        from config.asgi import application
        @database_sync_to_async
        def setup_order():
            order=Order.objects.create(customer=self.customer,restaurant=self.r,address='Rua A',delivery_fee=0,total=20)
            return order.pk,str(AccessToken.for_user(self.customer)),str(AccessToken.for_user(self.other))
        pk,token,other=await setup_order()
        rejected=WebsocketCommunicator(application,f'/ws/orders/{pk}/?token={other}',headers=[(b'origin',b'http://localhost')])
        connected,_=await rejected.connect()
        self.assertFalse(connected)
        socket=WebsocketCommunicator(application,f'/ws/orders/{pk}/?token={token}',headers=[(b'origin',b'http://localhost')])
        connected,_=await socket.connect()
        self.assertTrue(connected)
        await get_channel_layer().group_send(f'order_{pk}',{'type':'order.update','id':pk,'status':'preparing'})
        self.assertEqual((await socket.receive_json_from())['status'],'preparing')
        await socket.disconnect()
