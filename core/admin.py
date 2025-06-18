from django.contrib import admin
from .models import UserActivity,AppSettings

# Register your models here.
admin.site.register(UserActivity)
admin.site.register(AppSettings)