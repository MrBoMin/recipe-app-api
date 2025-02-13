"""Tet for recipe APIS"""



from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


from rest_framework import status
from rest_framework.test import APIClient
from core.models import Recipe
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Create and return the detail URL."""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a sample recipe"""
    default = {
        'title' : 'Sample Recipe Title',
        'time_minutes' : 22 ,
        'price' : Decimal('5.25'),
        'description' : 'Sample Description',
        'link' : 'http://example.com/recipe.pdf'
    }
    default.update(params)
    recipe = Recipe.objects.create(user=user, **default)
    return recipe


def create_user(**params):
    user = get_user_model().objects.create_user(
        email = params.get('email'),
        password = params.get('password')
    )
    return user

class PublicRecipeAPITests(TestCase):
    """Test unauthicated API Requests """
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API"""
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)



class PrivateRecipeAPITests(TestCase):
    """Test Authenticated API Requests."""
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email= 'user@example.com',password = 'testpass123')
        self.client.force_authenticate(self.user)

    def test_retrive_recipes(self):
        """Test create and retrive recipes """

        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK )


    def test_recipe_list_limited_user(self):
        """Test lst of recipes is limited to authenticated user."""
        other_user = create_user(email = 'other@example.com',password ='testing123')
        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK )

    def test_retrive_recipes_detail(self):
        """Test for retriveing detailed serializer"""
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe_id=recipe.id)
        res = self.client.get(url)
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_recipe(self):
        """Testing creating a recipe"""
        payload = {
            'title' : 'Sample Recipe',
            'time_minutes' : 30,
            'price' : Decimal('5.59'),
        }
        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe =Recipe.objects.get(id = res.data.get('id'))
        for k,v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user,self.user)

    def test_partial_update(self):
        """Testing the partial update of recipe"""
        original_link ='https://example.com/recipe.pdf'
        recipe = create_recipe(
            user= self.user,
            title = 'hello',
            link = original_link
        )
        payload = {'title' : 'new tile'}
        url = detail_url(recipe_id=recipe.id)
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload.get('title'))
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """Testing the full update for update"""
        recipe = create_recipe(user=self.user)
        payload = {
            'title' : 'new title',
            'description' : 'new description',
            'time_minutes' : 32,
            'price' : Decimal('4.23'),
            'link' : 'https://example.com/new.pdf'
        }

        url = detail_url(recipe_id=recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()

        for k,v in payload.items():
            self.assertEqual(getattr(recipe,k), v)
        self.assertEqual(self.user, recipe.user)


    def test_update_user_returns_error(self):
        '''Test when updaing the user, it should return error'''
        new_user = create_user(email='newuser@example.com', password = 'test123')
        recipe = create_recipe(user=self.user)

        payload = {
            'user' : new_user.id
        }

        url = detail_url(recipe_id=recipe.id)
        res = self.client.patch(url,payload)
        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        recipe = create_recipe(user = self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())