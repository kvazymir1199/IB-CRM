from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
import json
from .models import SeasonalSignal, Symbol
from .serializers import SeasonalSignalSerializer, SymbolSerializer


# Словарь для отображения месяцев
MONTHS = {
    1: "Январь",
    2: "Февраль",
    3: "Март",
    4: "Апрель",
    5: "Май",
    6: "Июнь",
    7: "Июль",
    8: "Август",
    9: "Сентябрь",
    10: "Октябрь",
    11: "Ноябрь",
    12: "Декабрь",
}


@ensure_csrf_cookie
def home(request):
    signals = SeasonalSignal.objects.all().order_by("-id")
    return render(request, "signals/home.html", {"signals": signals, "months": MONTHS})


def signal_detail(request, signal_id):
    signal = get_object_or_404(SeasonalSignal, id=signal_id)
    symbols = Symbol.objects.all().order_by("financial_instrument")
    return render(
        request,
        "signals/signal_detail.html",
        {"signal": signal, "symbols": symbols, "months": MONTHS},
    )


class SymbolViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Symbol.objects.all().order_by("financial_instrument")
    serializer_class = SymbolSerializer


class SeasonalSignalViewSet(viewsets.ModelViewSet):
    queryset = SeasonalSignal.objects.all()
    serializer_class = SeasonalSignalSerializer

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(
                {"id": serializer.instance.id, "message": "Сигнал успешно создан"},
                status=status.HTTP_201_CREATED,
            )
        except IntegrityError as e:
            if "UNIQUE constraint" in str(e):
                return Response(
                    {"error": "Сигнал с таким Magic Number уже существует"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {"error": "Ошибка при сохранении сигнала"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@require_http_methods(["PUT", "POST"])
def update_signal(request, signal_id):
    try:
        signal = get_object_or_404(SeasonalSignal, id=signal_id)

        # Получаем данные из JSON
        data = json.loads(request.body)

        # Обновляем поля сигнала
        for field, value in data.items():
            if hasattr(signal, field):
                setattr(signal, field, value)

        # Сохраняем изменения
        signal.full_clean()  # Проверяем валидность данных
        signal.save()

        return JsonResponse({"message": "Сигнал успешно обновлен", "id": signal.id})
    except ValidationError as e:
        return JsonResponse(
            {"error": "Ошибка валидации: " + ", ".join(e.messages)}, status=400
        )
    except json.JSONDecodeError:
        return JsonResponse({"error": "Неверный формат JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
