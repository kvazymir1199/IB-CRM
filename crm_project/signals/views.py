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
    1: 'January',
    2: 'February',
    3: 'March',
    4: 'April',
    5: 'May',
    6: 'June',
    7: 'July',
    8: 'August',
    9: 'September',
    10: 'October',
    11: 'November',
    12: 'December'
}


@ensure_csrf_cookie
def home(request):
    signals = SeasonalSignal.objects.all().order_by("-id")
    return render(
        request, 
        "signals/home.html", 
        {"signals": signals, "months": MONTHS}
    )


def signal_detail(request, signal_id):
    signal = get_object_or_404(SeasonalSignal, id=signal_id)
    symbols = Symbol.objects.all().order_by("financial_instrument")
    return render(
        request, 
        "signals/signal_detail.html", 
        {
            "signal": signal, 
            "symbols": symbols,
            "months": MONTHS
        }
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
                {
                    "id": serializer.instance.id, 
                    "message": "Signal created successfully"
                },
                status=status.HTTP_201_CREATED,
            )
        except IntegrityError as e:
            if "UNIQUE constraint" in str(e):
                return Response(
                    {"error": "Signal with this Magic Number already exists"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {"error": "Error saving signal"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response({
                "message": "Signal updated successfully",
                "id": instance.id
            })
        except ValidationError as e:
            return Response(
                {
                    "error": "Validation error: " + ", ".join(e.messages)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
