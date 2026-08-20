from rest_framework import serializers


class CurrencyRatesSerializer(serializers.Serializer):
    base = serializers.CharField()
    rates = serializers.DictField(child=serializers.FloatField())


class CurrencyConvertResultSerializer(serializers.Serializer):
    amount_npr = serializers.FloatField()
    to = serializers.CharField()
    converted = serializers.FloatField()
    rate = serializers.FloatField()
