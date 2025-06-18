from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UserActivity(models.Model):
    ACTIVITY_TYPES = [
        ('product_created', 'Product Created'),
        ('product_updated', 'Product Updated'),
        ('product_published', 'Product Published'),
        ('channel_connected', 'Channel Connected'),
        ('social_post_created', 'Social Post Created'),
        ('social_post_published', 'Social Post Published'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    description = models.TextField()
    
    # Optional reference to related objects
    object_id = models.CharField(max_length=100, blank=True)
    object_type = models.CharField(max_length=50, blank=True)  # 'product', 'channel', etc.
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.email} - {self.get_activity_type_display()}"

class AppSettings(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.key