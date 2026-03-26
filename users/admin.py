from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Profile Info', {'fields': ('role', 'phone_number')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Extra Profile Info', {'fields': ('role', 'phone_number')}),
    )

    list_display = ('username', 'email', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')
