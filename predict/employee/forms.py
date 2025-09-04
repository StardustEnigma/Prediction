from django import forms
from .models import EmployeeAttrition


class EmployeeAttritionForm(forms.ModelForm):
    class Meta:
        model = EmployeeAttrition
        # exclude attrition so it will be set by ML model
        exclude = ['attrition']  
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'min': 18, 'max': 65}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'marital_status': forms.Select(attrs={'class': 'form-select'}),
            'job_satisfaction': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'working_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'years_at_company': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'distance_from_home': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'environment_satisfaction': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'health_condition': forms.Select(attrs={'class': 'form-select'}),
            'expectations_from_company': forms.Select(attrs={'class': 'form-select'}),
            'joining_salary': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'current_salary': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'education': forms.Select(attrs={'class': 'form-select'}),

            # 🆕 Extra fields often found in attrition models
            'department': forms.Select(attrs={'class': 'form-select'}),
            'job_role': forms.Select(attrs={'class': 'form-select'}),
            'overtime': forms.Select(attrs={'class': 'form-select'}),
            'performance_rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'training_times_last_year': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'work_life_balance': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'stock_option_level': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply bootstrap classes consistently
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
                field.empty_label = None  # removes the "---------" option
            else:
                field.widget.attrs.update({'class': 'form-control'})
