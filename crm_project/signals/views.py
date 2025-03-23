from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.db import IntegrityError
import json
from .models import SeasonalSignal


@ensure_csrf_cookie
def home(request):
    signals = SeasonalSignal.objects.all().order_by('-id')
    return render(request, 'signals/home.html', {'signals': signals})


def signal_detail(request, signal_id):
    signal = get_object_or_404(SeasonalSignal, id=signal_id)
    return render(request, 'signals/signal_detail.html', {'signal': signal})


@require_http_methods(['POST'])
def create_seasonal_signal(request):
    try:
        data = json.loads(request.body)
        signal = SeasonalSignal.objects.create(**data)
        return JsonResponse({
            'id': signal.id,
            'message': 'Сигнал успешно создан'
        }, status=201)
    except IntegrityError as e:
        if 'UNIQUE constraint' in str(e):
            return JsonResponse({
                'error': 'Сигнал с таким Magic Number уже существует'
            }, status=400)
        return JsonResponse({
            'error': 'Ошибка при сохранении сигнала'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)
