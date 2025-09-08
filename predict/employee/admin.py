from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import President, EmployeeAttrition


# Register EmployeeAttrition with enhanced display
@admin.register(EmployeeAttrition)
class EmployeeAttritionAdmin(admin.ModelAdmin):
    list_display = (
        'employee_id', 
        'name', 
        'age', 
        'gender', 
        'marital_status', 
        'attrition', 
        'attrition_probability_display',
        'retention_status_display',
        'data_source'
    )
    
    list_filter = (
        'gender', 
        'marital_status', 
        'attrition', 
        'data_source',
        'is_retained'
    )
    
    search_fields = ('employee_id', 'name')
    ordering = ('employee_id',)
    
    # ✅ FIXED: Build string first, then pass to format_html
    def attrition_probability_display(self, obj):
        """Display attrition risk percentage with color coding"""
        if obj.attrition_probability is None:
            return "N/A"
        
        try:
            risk_value = float(obj.attrition_probability)
        except (ValueError, TypeError):
            return "Error"
        
        # Determine color and icon based on risk level
        if risk_value >= 75:
            color = 'red'
            icon = '🔴'
        elif risk_value >= 50:
            color = 'orange'
            icon = '🟡'
        else:
            color = 'green'
            icon = '🟢'
        
        # ✅ KEY FIX: Format the string BEFORE calling format_html
        display_text = f"{icon} {risk_value:.1f}%"
        
        # Now pass the formatted string to format_html
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>', 
            color, display_text
        )
    
    attrition_probability_display.short_description = 'Attrition Risk (%)'
    attrition_probability_display.admin_order_field = 'attrition_probability'
    
    # ✅ Display retention status with visual indicators
    def retention_status_display(self, obj):
        """Display retention status with visual indicators"""
        if obj.is_retained:
            return format_html(
                '<span style="color: green; font-weight: bold;">✅ RETAINED</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ AT-RISK</span>'
            )
    
    retention_status_display.short_description = 'Status'
    retention_status_display.admin_order_field = 'is_retained'


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
