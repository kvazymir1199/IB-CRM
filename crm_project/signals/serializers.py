from rest_framework import serializers
from .models import SeasonalSignal


class SeasonalSignalSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeasonalSignal
        fields = '__all__'
        read_only_fields = ('id',) 