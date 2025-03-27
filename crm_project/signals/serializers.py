from rest_framework import serializers
from .models import SeasonalSignal, Symbol


class SymbolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symbol
        fields = '__all__'


class SeasonalSignalSerializer(serializers.ModelSerializer):
    symbol_details = SymbolSerializer(source='symbol', read_only=True)

    class Meta:
        model = SeasonalSignal
        fields = '__all__'
        read_only_fields = ('id',) 