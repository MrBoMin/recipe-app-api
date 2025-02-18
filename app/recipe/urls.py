from rest_framework.routers import DefaultRouter
from .views import RecipeViewSet, TagViewSet,IngredientViewSet

router = DefaultRouter()

router.register(r'recipes', RecipeViewSet)
router.register(r'tags', TagViewSet)
router.register(r'ingredients', IngredientViewSet)

app_name = 'recipe'

urlpatterns = router.urls