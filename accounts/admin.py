from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'plan_type', 'business_name', 'is_active', 'date_joined')
    list_filter = ('plan_type', 'is_active', 'date_joined', 'is_staff')
    search_fields = ('email', 'username', 'business_name', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Business Info', {
            'fields': ('business_name', 'phone', 'plan_type')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Business Info', {
            'fields': ('email', 'business_name', 'phone', 'plan_type')
        }),
    )