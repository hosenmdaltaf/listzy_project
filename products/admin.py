from django.contrib import admin
from .models import Product, ProductImage, ProductTag, ProductTagging

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_primary', 'order')

class ProductTaggingInline(admin.TabularInline):
    model = ProductTagging
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'price', 'sku', 'is_active', 'is_featured', 'created_at')
    list_filter = ('is_active', 'is_featured', 'created_at', 'updated_at')
    search_fields = ('title', 'description', 'sku', 'user__email')
    list_editable = ('is_active', 'is_featured')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [ProductImageInline, ProductTaggingInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'description', 'price', 'sku')
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('AI Generated', {
            'fields': ('ai_generated_description', 'ai_generated_hashtags'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'alt_text', 'is_primary', 'order', 'created_at')
    list_filter = ('is_primary', 'created_at')
    search_fields = ('product__title', 'alt_text')

@admin.register(ProductTag)
class ProductTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}