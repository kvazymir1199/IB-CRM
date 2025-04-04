from django.urls import path
from . import views

app_name = 'trading_bot'

urlpatterns = [
    path('api/bot/state/', views.get_bot_state, name='get_bot_state'),
    path('api/bot/toggle/', views.toggle_bot_state, name='toggle_bot_state'),
] 