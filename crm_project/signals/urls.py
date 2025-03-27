from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'signals'

# Создаем router для API
router = DefaultRouter()
router.register(r'seasonal', views.SeasonalSignalViewSet, basename='seasonal-signal')
router.register(r'symbols', views.SymbolViewSet, basename='symbol')

urlpatterns = [
    path('', views.home, name='home'),
    path('signal/<int:signal_id>/', views.signal_detail, name='signal_detail'),
    # Включаем URL-ы из router
    path('api/signals/', include(router.urls)),
] 