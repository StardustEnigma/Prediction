from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import President, EmployeeAttrition

# Register EmployeeAttrition
@admin.register(EmployeeAttrition)
class EmployeeAttritionAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'name', 'age', 'gender', 'marital_status', 'attrition', 'data_source')
    list_filter = ('gender', 'marital_status', 'attrition', 'data_source')
    search_fields = ('employee_id', 'name')
    ordering = ('employee_id',)

# Register President with UserAdmin
@admin.register(President)
class PresidentAdmin(UserAdmin):
    model = President
    list_display = ('username', 'email', 'is_active_president', 'is_staff', 'is_superuser')
    list_filter = ('is_active_president', 'is_staff', 'is_superuser')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Permissions', {'fields': ('is_active_president', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_active_president', 'is_staff', 'is_superuser')}
        ),
    )
    search_fields = ('username', 'email')
    ordering = ('username',)
