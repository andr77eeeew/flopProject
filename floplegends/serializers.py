from rest_framework import serializers
from .models import flopLegendsModel


class flopLegendsSerializer(serializers.ModelSerializer):
    class Meta:
        model = flopLegendsModel
        fields = '__all__'


class CreateflopLegendsSerializer(serializers.ModelSerializer):
    class Meta:
        model = flopLegendsModel
        fields = ('title', 'description', 'creator')
        extra_kwargs = {'creator': {'required': True}}

    def create(self, validated_data):
        creator = validated_data.pop('creator')
        flop = flopLegendsModel.objects.create(
            title=validated_data['title'],
            description=validated_data['description'],
            creator=creator
        )
        return flop
