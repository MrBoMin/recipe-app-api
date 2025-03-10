'''
Views for the recipes API
'''

from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from core.models import Recipe,Tag, Ingredient
from recipe import serializers
from .serializers import RecipeSerializer,RecipeDetailSerializer, TagSerializer, IngredientSerializer, RecipeImageSerializer
from rest_framework.decorators import action
from rest_framework.response import Response


@extend_schema_view(
    list = extend_schema(
        parameters = [
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR, 
                description = 'Comman Seperated List of IDs to Filter'
            ),
            OpenApiParameter(
                'ingredients',
                OpenApiTypes.STR,
                description = "comman seperated list of ingreident IDs to Filter"
            )
        ]
    )
)
class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()  # Order by ID in descending order
    serializer_class = RecipeDetailSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self,qs):
        """Conver a list of string to integers"""
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """Retrive the recipes for authenticated user """
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        queryset = self.queryset 
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in = tag_ids)
        if ingredients:
            ingredients_id = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in = ingredients_id) 

        return queryset.filter(
            user = self.request.user
        ).order_by('-id').distinct()

    def get_serializer_class(self):
        """Return the searlizer class for request"""
        if self.action == 'list':
            return serializers.RecipeSerializer
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer

        return self.serializer_class

    def perform_create(self,serializer):
        """Create the new object for authenticated user"""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self,request, pk=None):
        """Upload an image to a recipe"""
        recipe = self.get_object()
        serializer = self.get_serializer(recipe, data = request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status = status.HTTP_200_OK)
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma separated list of tag IDs to filter',
            ),
            OpenApiParameter(
                'ingredients',
                OpenApiTypes.STR,
                description='Comma separated list of ingredient IDs to filter',
            ),
        ]
    ),
    upload_image=extend_schema(
        request=RecipeImageSerializer,
        responses={status.HTTP_200_OK: RecipeImageSerializer},
    ),
)

class BaseRecipeAttrViewSet(mixins.DestroyModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    """Base viewset for recipe attributes."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        '''Filter the query set to authenticated user'''
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(recipes__isnull=False)

        return queryset.filter(
            user=self.request.user
        ).order_by('-name').distinct()

class TagViewSet(BaseRecipeAttrViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

class IngredientViewSet(BaseRecipeAttrViewSet):
    """manage the ingredients in the database"""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
