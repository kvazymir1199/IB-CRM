from django.urls import path
from . import views

app_name = "signals"

urlpatterns = [
    path("", views.home, name="home"),
    path("signal/<int:signal_id>/", views.signal_detail, name="signal_detail"),
    path(
        "api/signals/seasonal/",
        views.create_seasonal_signal,
        name="create_seasonal_signal",
    ),
    path(
        "api/signals/seasonal/<int:signal_id>/",
        views.update_signal,
        name="update_signal",
    ),
]
