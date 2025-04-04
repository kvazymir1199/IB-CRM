from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import BotState

# Create your views here.

@require_http_methods(["GET"])
def get_bot_state(request):
    """Получить текущее состояние бота"""
    state = BotState.get_state()
    return JsonResponse({
        'is_running': state.is_running,
        'last_updated': state.last_updated.isoformat()
    })

@require_http_methods(["POST"])
def toggle_bot_state(request):
    """Переключить состояние бота"""
    state = BotState.get_state()
    state.is_running = not state.is_running
    state.save()
    return JsonResponse({
        'is_running': state.is_running,
        'last_updated': state.last_updated.isoformat()
    })
