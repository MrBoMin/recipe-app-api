''' Serializer for Recipe API '''

from rest_framework import serializers

from core.models import Recipe, Tag



class RecipeSerializer(serializers.ModelSerializer):
    '''Serializer for Recipe'''
    class Meta:
        model = Recipe
        fields = ['id','title','time_minutes','price','link']
        read_only_field = ['id']

class RecipeDetailSerializer(RecipeSerializer):
    '''Detail Serailzer for one Recipe'''
    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']


class TagSerializer(serializers.ModelSerializer):
    '''Serializers for Tags'''
    class Meta:
        model = Tag
        fields = ['id','name']
        read_only_field = ['id']


