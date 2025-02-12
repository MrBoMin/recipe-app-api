'''
Views for the user API.
'''


from rest_framework import generics
from user.serializers import UserSerializer


class CreateUserView(generics.CreateAPIView):
    """Create a new user int he system"""
    serializer_class  = UserSerializer


