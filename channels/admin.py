from django.contrib import admin
from .models import ConnectedChannel, ProductListing

@admin.register(ConnectedChannel)
class ConnectedChannelAdmin(admin.ModelAdmin):
    list_display = ('user', 'platform', 'platform_username', 'status', 'connected_at')
    list_filter = ('platform', 'status', 'connected_at')
    search_fields = ('user__email', 'platform_username', 'shop_name')
    readonly_fields = ('id', 'connected_at', 'updated_at')
    
    fieldsets = (
        ('Connection Info', {
            'fields': ('user', 'platform', 'status')
        }),
        ('Platform Details', {
            'fields': ('platform_user_id', 'platform_username', 'shop_name', 'shop_url')
        }),
        ('OAuth Tokens', {
            'fields': ('access_token', 'refresh_token', 'token_expires_at'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('last_sync', 'error_message')
        }),
        ('Metadata', {
            'fields': ('id', 'connected_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(ProductListing)
class ProductListingAdmin(admin.ModelAdmin):
    list_display = ('product', 'channel', 'status', 'platform_product_id', 'last_synced')
    list_filter = ('status', 'channel__platform', 'created_at', 'last_synced')
    search_fields = ('product__title', 'platform_product_id', 'platform_url')
    readonly_fields = ('id', 'created_at', 'updated_at')