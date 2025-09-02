from django.db import models

from django.db import models

class EmployeeAttrition(models.Model):
    employee_id = models.CharField(max_length=20, unique=True)  # if you want to store EmployeeID
    age = models.PositiveIntegerField()
    
    GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female')]
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)
    
    MARITAL_STATUS_CHOICES = [('Single', 'Single'), ('Married', 'Married'), ('Divorced', 'Divorced')]
    marital_status = models.CharField(max_length=8, choices=MARITAL_STATUS_CHOICES)
    
    job_satisfaction = models.PositiveSmallIntegerField()  # 1-5 scale
    
    working_hours = models.PositiveIntegerField()
    
    years_at_company = models.PositiveIntegerField()
    
    distance_from_home = models.PositiveIntegerField()
    
    environment_satisfaction = models.PositiveSmallIntegerField()  # 1-5 scale
    
    HEALTH_CONDITION_CHOICES = [('Poor', 'Poor'), ('Average', 'Average'), ('Good', 'Good'), ('Excellent', 'Excellent')]
    health_condition = models.CharField(max_length=10, choices=HEALTH_CONDITION_CHOICES)
    
    EXPECTATIONS_CHOICES = [
        ('Health Benefits', 'Health Benefits'),
        ('Promotion', 'Promotion'),
        ('Flexible Work', 'Flexible Work'),
        ('Training', 'Training'),
        ('Work-Life Balance', 'Work-Life Balance')
    ]
    expectations_from_company = models.CharField(max_length=20, choices=EXPECTATIONS_CHOICES)
    
    joining_salary = models.PositiveIntegerField()
    
    current_salary = models.PositiveIntegerField()
    
    EDUCATION_CHOICES = [('High School', 'High School'), ('Bachelor', 'Bachelor'), ('Master', 'Master'), ('PhD', 'PhD')]
    education = models.CharField(max_length=12, choices=EDUCATION_CHOICES)
    
    attrition = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.employee_id} - {self.marital_status}"

