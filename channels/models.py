from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

class ConnectedChannel(models.Model):
    PLATFORM_CHOICES = [
        ('shopify', 'Shopify'),
        ('etsy', 'Etsy'),
        ('woocommerce', 'WooCommerce'),
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('tiktok', 'TikTok'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error'),
        ('expired', 'Token Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='channels')
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    
    # OAuth tokens
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Platform-specific data
    platform_user_id = models.CharField(max_length=100, blank=True)
    platform_username = models.CharField(max_length=100, blank=True)
    shop_name = models.CharField(max_length=100, blank=True)  # For Shopify/Etsy
    shop_url = models.URLField(blank=True)
    
    # Connection status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    last_sync = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Metadata
    connected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'platform', 'platform_user_id')
        
    def __str__(self):
        return f"{self.user.email} - {self.get_platform_display()}"
    
    @property
    def is_marketplace(self):
        return self.platform in ['shopify', 'etsy', 'woocommerce']
    
    @property
    def is_social(self):
        return self.platform in ['instagram', 'facebook', 'tiktok']
    
    @property
    def is_token_expired(self):
        if not self.token_expires_at:
            return False
        return timezone.now() > self.token_expires_at

class ProductListing(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('published', 'Published'),
        ('failed', 'Failed'),
        ('draft', 'Draft'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='listings')
    channel = models.ForeignKey(ConnectedChannel, on_delete=models.CASCADE, related_name='listings')
    
    # Platform-specific IDs
    platform_product_id = models.CharField(max_length=100, blank=True)
    platform_url = models.URLField(blank=True)
    
    # Listing data (can be customized per platform)
    custom_title = models.CharField(max_length=200, blank=True)
    custom_description = models.TextField(blank=True)
    custom_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    custom_tags = models.TextField(blank=True)  # JSON or comma-separated
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    
    # Sync tracking
    last_synced = models.DateTimeField(null=True, blank=True)
    sync_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('product', 'channel')
        
    def __str__(self):
        return f"{self.product.title} on {self.channel.get_platform_display()}"
    
    @property
    def effective_title(self):
        return self.custom_title or self.product.title
    
    @property
    def effective_description(self):
        return self.custom_description or self.product.description
    
    @property
    def effective_price(self):
        return self.custom_price or self.product.price