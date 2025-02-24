"""Tet for recipe APIS"""



from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


from rest_framework import status
from rest_framework.test import APIClient
from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer
import tempfile
import os
from PIL import Image

RECIPES_URL = reverse('recipe:recipe-list')


def image_upload_url(recipe_id):
    """Create and return the detail URL of image upload """
    return reverse('recipe:recipe-upload-image', args = [recipe_id])


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

    def test_delete_other_users_recipe_error(self):
        """Test trying to delete another users recipe gives errors"""
        new_user = create_user(email='user2@example.com',password='testpass123')
        recipe = create_recipe(user=new_user)
        url = detail_url(recipe_id=recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())


    def test_create_recipe_with_new_tags(self):
        """Test creating a recipe with new tags"""
        payload = {
            'title' : 'Thai Prawn Curry',
            'time_minutes' : 30,
            'price' : Decimal('2.50'),
            'tags' : [{'name' : 'Thai'}, {'name' : 'Dinner'}]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user = self.user)
        self.assertEqual(recipes.count(),1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(),2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name = tag['name'],
                user = self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test and create a recipe with existing tags."""
        tag_indian = Tag.objects.create(user=self.user, name ="Indian")
        payload = {
            'title' : 'Pongal',
            'time_minutes' : 60,
            'price' : Decimal('4.50'),
            'tags' : [{'name' : 'Indian'},{'name' : 'Breakfast'}]
        }
        res = self.client.post(RECIPES_URL,payload, format = 'json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user = self.user)
        self.assertEqual(recipes.count(),1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(),2)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name = tag['name'],
                user = self.user
            ).exists()
            self.assertTrue(exists)


    def test_create_tag_on_update(self):
        """Test creating tag when upading a recipe"""
        recipe = create_recipe(user = self.user)

        payload = {'tags' : [{'name' : 'Lunch'}]}
        url = detail_url(recipe_id=recipe.id)
        res = self.client.patch(url, payload, format = 'json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Lunch')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Testing assinging an existing tag when updating a recipe"""
        tag_breakfast = Tag.objects.create(user=self.user, name = "Breakfast")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user =self.user, name = "Lunch")
        payload = {'tags' : [{'name' : 'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())


    def test_clear_recipe_tags(self):
        """Test clearing a recipe tags"""
        tag = Tag.objects.create(user = self.user, name = 'Dessert')
        recipe = create_recipe(user = self.user)
        recipe.tags.add(tag)

        payload = {'tags' : []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format = 'json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)


    def test_create_recipe_with_new_ingredients(self):
        """Test creatting a recipe with new ingredients"""
        payload = {
            'title' : 'Cauliflower Tacos',
            'time_minutes' : 60,
            'price' : Decimal('4.30'),
            'ingredients' : [{'name' : 'Cauliflower'}, {'name' : 'Salt'}]

        }
        res = self.client.post(RECIPES_URL, payload, format = 'json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user = self.user)
        self.assertEqual(recipes.count(),1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(),2)
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name = ingredient['name'],
                user = self.user,
            ).exists()
            self.assertTrue(exists)


    def test_create_recipe_with_existing_ingredient(self):
        """Test creating a new recipe with existing ingredient"""
        ingredient  = Ingredient.objects.create(user = self.user, name = 'Lemon')
        payload = {
            'title' : 'Vietnamese Soup',
            'time_minutes' : 25,
            'price' : '2.55',
            'ingredients' : [{'name' : 'Lemon'},{'name' : 'Fish Sauce+'}]
        }

        res = self.client.post(RECIPES_URL, payload, format = 'json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user = self.user)
        self.assertEqual(recipes.count(),1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(),2)
        self.assertIn(ingredient, recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(name = ingredient['name'] , user = self.user).exists()
            self.assertTrue(exists)



    def test_create_ingredient_on_update(self):
        """Test creating an ingredient when updaing a recipe."""
        recipe = create_recipe(self.user)
        payload = {'ingredients' : [{'name' : 'Limes'}]}
        url = detail_url(recipe_id=recipe.id)
        res = self.client.patch(url, payload, format = 'json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user = self.user, name = 'Limes')
        self.assertIn(new_ingredient, recipe.ingredients.all())


    def test_update_recipe_assign_ingredient(self):
        """Test assigning an existing ingredient when updating a recipe"""
        ingredient1 = Ingredient.objects.create(user = self.user , name = 'Pepper')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user = self.user , name = "Chili")
        payload = {'ingredients' : [{'name' : 'Chili'}]}
        url = detail_url(recipe_id=recipe.id)
        res = self.client.patch(url, payload , format = 'json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())


    def test_clear_recipe_ingredients(self):
        """Test clearing a recipe ingredients"""
        ingredient = Ingredient.objects.create(user = self.user, name = 'Garlic')
        recipe = create_recipe(user =self.user)
        recipe.ingredients.add(ingredient)
        payload = {'ingredients' : []}
        url = detail_url(recipe.id)
        res = self.client.patch(url,payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(),0)

    def test_filter_by_tags(self):
        """Test filter recipes by tags"""
        r1 = create_recipe(user = self.user, title = "Thai Vegetable Curry")
        r2 = create_recipe(user = self.user, title = 'Aubergian with Tahini')
        tag1 = Tag.objects.create(user = self.user, name = "Vegan")
        tag2 = Tag.objects.create(user = self.user, name = "Vegetarian")
        r1.tags.add(tag1)
        r2.tags.add(tag2)
        r3 = create_recipe(user = self.user, title = "Fish and Chips")

        params = {'tags' : f'{tag1.id}, {tag2.id}'}
        res = self.client.get(RECIPES_URL, params) 

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_by_ingredients(self):
        r1 = create_recipe(user = self.user, title = "Posh Beans on Toast")
        r2 = create_recipe(user = self.user, title = "Chieck")
        in1 = Ingredient.objects.create(user = self.user, name = "Blah1")
        in2 = Ingredient.objects.create(user = self.user, name = "Blah2")
        r3 = create_recipe(user = self.user, title = "asdfasdf")
        r1.ingredients.add(in1)
        r2.ingredients.add(in2)
        params = {'ingredients' : f'{in1.id},{in2.id}'}
        res = self.client.get(RECIPES_URL, params)
        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)



class ImageUploadTests(TestCase):
    """Testing for image uploading"""
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user('user@example.com','testpass123')
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading a image to a recipe"""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB',(10,10))
            img.save(image_file,format = 'JPEG')
            image_file.seek(0)
            payload = {'image' : image_file}
            res = self.client.post(url, payload, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_image_upload_bad_request(self):
        url = image_upload_url(self.recipe.id)
        payload = {'image' : 'notanimage'}
        res = self.client.post(url, payload, format = 'multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


    