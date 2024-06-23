from rest_framework import serializers
from .models import flopLegendsModel





class flopLegendsSerializer(serializers.ModelSerializer):
    creator_username = serializers.SerializerMethodField()

    class Meta:
        model = flopLegendsModel
        fields = ['id', 'title', 'description', 'creator', 'creator_username']

    def get_creator_username(self, obj):
        return obj.creator.username


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
