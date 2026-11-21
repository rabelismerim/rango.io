from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from core.views import RestaurantViewSet, ProductViewSet, OptionViewSet, OrderViewSet
router = DefaultRouter()
for name, view in [('restaurants', RestaurantViewSet), ('products', ProductViewSet), ('options', OptionViewSet), ('orders', OrderViewSet)]: router.register(name, view)
urlpatterns = [path('admin/', admin.site.urls), path('api/', include(router.urls)), path('api/token/', TokenObtainPairView.as_view()), path('api/token/refresh/', TokenRefreshView.as_view()), path('api/schema/', SpectacularAPIView.as_view(), name='schema'), path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'))]
