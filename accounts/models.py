from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    PLAN_CHOICES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional profile fields
    business_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.email
    
    @property
    def display_name(self):
        return self.business_name or self.get_full_name() or self.username