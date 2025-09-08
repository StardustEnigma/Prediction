from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission


# Custom President user model
class President(AbstractUser):
    is_active_president = models.BooleanField(default=False)

    # Fix reverse accessor clashes
    groups = models.ManyToManyField(
        Group,
        related_name='president_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='president_permissions_set',
        blank=True
    )

    def __str__(self):
        return self.username


# Employee attrition data model
class EmployeeAttrition(models.Model):
    employee_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100, default='Unknown')
    age = models.PositiveIntegerField()

    GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female')]
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, default='Male')

    MARITAL_STATUS_CHOICES = [
        ('Single', 'Single'),
        ('Married', 'Married'),
        ('Divorced', 'Divorced')
    ]
    marital_status = models.CharField(max_length=8, choices=MARITAL_STATUS_CHOICES, default='Single')

    job_satisfaction = models.PositiveSmallIntegerField()  # 1-5 scale
    working_hours = models.PositiveIntegerField()
    years_at_company = models.PositiveIntegerField()
    distance_from_home = models.PositiveIntegerField()
    environment_satisfaction = models.PositiveSmallIntegerField()  # 1-5 scale

    HEALTH_CONDITION_CHOICES = [
        ('Poor', 'Poor'),
        ('Average', 'Average'),
        ('Good', 'Good'),
        ('Excellent', 'Excellent')
    ]
    health_condition = models.CharField(max_length=10, choices=HEALTH_CONDITION_CHOICES, default='Average')

    EXPECTATIONS_CHOICES = [
        ('Health Benefits', 'Health Benefits'),
        ('Promotion', 'Promotion'),
        ('Flexible Work', 'Flexible Work'),
        ('Training', 'Training'),
        ('Work-Life Balance', 'Work-Life Balance')
    ]
    expectations_from_company = models.CharField(
        max_length=20,
        choices=EXPECTATIONS_CHOICES,
        default='Work-Life Balance'
    )

    joining_salary = models.PositiveIntegerField()
    current_salary = models.PositiveIntegerField()

    EDUCATION_CHOICES = [
        ('High School', 'High School'),
        ('Bachelor', 'Bachelor'),
        ('Master', 'Master'),
        ('PhD', 'PhD')
    ]
    education = models.CharField(max_length=12, choices=EDUCATION_CHOICES, default='Bachelor')

    attrition = models.BooleanField(default=False)
    
    # ✅ NEW FIELDS - Add these two lines
    attrition_probability = models.FloatField(
        null=True, 
        blank=True, 
        help_text="ML-predicted attrition risk percentage"
    )
    is_retained = models.BooleanField(
        default=False, 
        help_text="Automatically set to True if attrition risk < 25%"
    )

    DATA_SOURCE_CHOICES = [
        ('Feedback Form', 'Feedback Form'),
        ('CSV', 'CSV')
    ]
    data_source = models.CharField(
        max_length=20,
        choices=DATA_SOURCE_CHOICES,
        default='Feedback Form'
    )

    created_at = models.DateTimeField(auto_now_add=True)  # ✅ Add timestamp

    def __str__(self):
        return f"{self.employee_id} - {self.name} - {self.marital_status}"

    class Meta:
        verbose_name = "Employee Attrition"
        verbose_name_plural = "Employee Attritions"
        ordering = ['-created_at']  # Show newest first
