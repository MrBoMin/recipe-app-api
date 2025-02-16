'''Testing Tag API '''

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


def detail_url(tag_id):
    """Create and return the detail url of a tag."""
    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(email="test@example.com", password="testpass123"):
    """Create and return the test user."""
    return get_user_model().objects.create_user(email,password)


class PublicTagsApiTests(TestCase):
    """Testing unauthenticated API Requests"""
    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test Auth is required for accessing the API"""
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateTagsApiTests(TestCase):
    """Testing the featuresf or authenticated users."""
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)


    def test_retreive_tags(self):
        """Testing the retreiving features"""
        Tag.objects.create(user = self.user, name = 'Vegan')
        Tag.objects.create(user = self.user, name = 'Dessert')

        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags , many=True)
        self.assertEqual(serializer.data, res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


    def test_tag_list_limited_user(self):
        """Testing the accessing tags from non-owner."""
        user2 = create_user('user2@example.com','testpass123')
        Tag.objects.create(user=user2, name = 'Vegan')
        tag = Tag.objects.create(user = self.user, name = 'Dessert')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data) , 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_tag_update(self):
        """Testing the upading tags"""
        tag = Tag.objects.create(user=self.user,name="After Dinner")
        payload = {
            'name' : 'Dessert'
        }
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])


    def test_tag_delete(self):
        """Testing the deleting tags"""
        tag = Tag.objects.create(user=self.user, name = 'Breakfast')
        url = detail_url(tag.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())


