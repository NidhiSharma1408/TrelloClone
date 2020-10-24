from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .validators import validate_name
class UserManager(BaseUserManager):
    use_in_migrations = True
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    username     = models.CharField(blank=True, null=True, max_length = 30)
    first_name   = models.CharField(blank=True, null=True,max_length=30)
    last_name    = models.CharField(blank=True, null=True,max_length=30)
    email        = models.EmailField('email address', unique=True)
    is_active    = models.BooleanField(default=False)
    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    objects = UserManager()
    def __str__(self):
        return self.email
        

class UserProfile(models.Model):
    user         = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name ='profile')
    name         = models.CharField(max_length = 30,blank=False,validators=[validate_name])
    picture      = models.ImageField(upload_to = 'profile/', blank = True, null = True, max_length = None)
    def __str__(self):
        return self.user.email
    

class OtpModel(models.Model):
    otp          = models.CharField(max_length = 6)
    otp_email    = models.EmailField()
    time_created = models.IntegerField()
    def __str__(self):
        return f"{self.otp_email} : {self.otp}"