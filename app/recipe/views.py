'''
Views for the recipes API
'''


from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from core.models import Recipe,Tag, Ingredient
from recipe import serializers
from .serializers import RecipeSerializer,RecipeDetailSerializer, TagSerializer, IngredientSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()  # Order by ID in descending order
    serializer_class = RecipeDetailSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrive the recipes for authenticated user """
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        """Return the searlizer class for request"""
        if self.action == 'list':
            return serializers.RecipeSerializer

        return self.serializer_class

    def perform_create(self,serializer):
        """Create the new object for authenticated user"""
        serializer.save(user=self.request.user)


class TagViewSet(mixins.DestroyModelMixin,mixins.UpdateModelMixin,mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retreive the tags for authenticated users"""
        return self.queryset.filter(user=self.request.user).order_by('-name')



class IngredientViewSet(mixins.DestroyModelMixin,mixins.UpdateModelMixin,mixins.ListModelMixin, viewsets.GenericViewSet):
    """manage the ingredients in the database"""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        '''Filter the query set to authenticated user'''
        return self.queryset.filter(user = self.request.user).order_by('-name')