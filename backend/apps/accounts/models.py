from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra):
        if not email:
            raise ValueError('Email obrigatório')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        extra.setdefault('is_admin', True)
        return self.create_user(email, name, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    email      = models.EmailField(unique=True)
    name       = models.CharField(max_length=150)
    phone      = models.CharField(max_length=20, blank=True)
    # Endereço
    zipcode    = models.CharField(max_length=10, blank=True)
    street     = models.CharField(max_length=200, blank=True)
    number     = models.CharField(max_length=10, blank=True)
    complement = models.CharField(max_length=100, blank=True)
    city       = models.CharField(max_length=100, blank=True)
    state      = models.CharField(max_length=2, blank=True)
    # Flags
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    is_admin   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['name']
    objects = UserManager()

    def __str__(self):
        return self.email
