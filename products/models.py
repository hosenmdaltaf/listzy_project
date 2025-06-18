from django.db import models
from django.contrib.auth import get_user_model
import uuid
from cloudinary.models import CloudinaryField

User = get_user_model()

class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    
    # Basic product info
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sku = models.CharField(max_length=100, blank=True)
    
    # Product status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # SEO fields
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=300, blank=True)
    
    # AI generated fields
    ai_generated_description = models.TextField(blank=True)
    ai_generated_hashtags = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return self.title
    
    @property
    def primary_image(self):
        return self.images.filter(is_primary=True).first()
    
    @property
    def all_images(self):
        return self.images.all().order_by('-is_primary', 'order')

class ProductImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    
    # Cloudinary image field
    image = CloudinaryField('image', folder='listzy/products/')
    alt_text = models.CharField(max_length=200, blank=True)
    
    # Image metadata
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', 'order']
        
    def __str__(self):
        return f"{self.product.title} - Image {self.order}"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary image per product
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product, 
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

class ProductTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class ProductTagging(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='tags')
    tag = models.ForeignKey(ProductTag, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('product', 'tag')