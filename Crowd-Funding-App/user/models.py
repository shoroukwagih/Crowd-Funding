from django.db import models
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.models import User

import uuid
from django.utils import timezone


# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,null=True)
    image = models.ImageField(default='default.jpg', upload_to='user/images', null=True)
    mobile = models.CharField(max_length=15, blank=True, null=True)


    # Instance methods
    def getImgURL(self): 
        return f"/media/{self.image}"


class AdditionalInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,default=None)
    birthdate = models.DateField()
    country = models.CharField(max_length=20)
    facebook = models.URLField(max_length=200)


class ProfileActivation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    auth_token = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username
    
class Activation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)

    def is_expired(self):
        return (timezone.now() - self.created_at).days >= 1

