from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

class SocialPost(models.Model):
    POST_TYPES = [
        ('product', 'Product Post'),
        ('story', 'Story'),
        ('reel', 'Reel/Video'),
        ('carousel', 'Carousel'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('published', 'Published'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='social_posts')
    channel = models.ForeignKey('channels.ConnectedChannel', on_delete=models.CASCADE, related_name='social_posts')
    
    # Post content
    post_type = models.CharField(max_length=20, choices=POST_TYPES, default='product')
    caption = models.TextField()
    hashtags = models.TextField(blank=True)
    
    # Scheduling
    scheduled_time = models.DateTimeField(null=True, blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    
    # Platform response
    platform_post_id = models.CharField(max_length=100, blank=True)
    platform_url = models.URLField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    error_message = models.TextField(blank=True)
    
    # Analytics (basic)
    views = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    comments = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.product.title} - {self.channel.get_platform_display()}"
    
    @property
    def is_scheduled(self):
        return self.status == 'scheduled' and self.scheduled_time
    
    @property
    def is_due_for_posting(self):
        if not self.is_scheduled:
            return False
        return timezone.now() >= self.scheduled_time

class SocialTemplate(models.Model):
    TEMPLATE_TYPES = [
        ('caption', 'Caption Template'),
        ('hashtag', 'Hashtag Set'),
        ('story', 'Story Template'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_templates')
    
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    content = models.TextField()
    
    # Template variables (for dynamic content)
    variables = models.JSONField(default=dict, blank=True)  # e.g., {product_name}, {price}
    
    # Usage tracking
    usage_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"