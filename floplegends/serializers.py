from rest_framework import serializers
from .models import flopLegendsModel


class flopLegendsSerializer(serializers.ModelSerializer):
    creator_username = serializers.SerializerMethodField()
    creator_avatar = serializers.SerializerMethodField()

    class Meta:
        model = flopLegendsModel
        fields = ['id', 'title', 'description', 'cover', 'creator', 'creator_username', 'creator_avatar']

    def get_creator_username(self, obj):
        return obj.creator.username

    def get_creator_avatar(self, obj):
        if obj.creator.avatar:
            return obj.creator.avatar.url


class CreateflopLegendsSerializer(serializers.ModelSerializer):
    class Meta:
        model = flopLegendsModel
        fields = ('title', 'description', 'cover')
        extra_kwargs = {'creator': {'required': False}}

    def create(self, validated_data):
        creator = validated_data.pop('creator')
        cover = validated_data.pop('cover')
        flop = flopLegendsModel.objects.create(
            title=validated_data['title'],
            description=validated_data['description'],
            cover=cover,
            creator=creator
        )
        return flop
