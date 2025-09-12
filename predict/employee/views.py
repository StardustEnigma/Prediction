import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from employee.models import President
from .forms import EmployeeAttritionForm, CSVUploadForm, SubAdminCreationForm
from .models import EmployeeAttrition
from .ml_utils import predictor
import csv
from django.http import HttpResponse
from django.db.models import Q
from django.utils import timezone
@login_required(login_url='custom_login')
def reports(request):
    # Get search query
    search_query = request.GET.get('search', '').strip()
    
    # Base queryset
    employees = EmployeeAttrition.objects.all().order_by('-created_at')
    
    # Apply search filter if provided
    if search_query:
        employees = employees.filter(
            Q(name__icontains=search_query) |
            Q(employee_id__icontains=search_query)
        )
    
    # Calculate statistics
    total_employees = employees.count()
    retained_employees = employees.filter(is_retained=True).count()
    attrition_employees = employees.filter(is_retained=False).count()
    
    # Risk categorization
    high_risk = employees.filter(attrition_probability__gte=75).count()
    medium_risk = employees.filter(attrition_probability__gte=50, attrition_probability__lt=75).count()
    low_risk = employees.filter(attrition_probability__lt=50).count()
    
    context = {
        'employees': employees,
        'search_query': search_query,
        'total_employees': total_employees,
        'retained_employees': retained_employees,
        'attrition_employees': attrition_employees,
        'high_risk': high_risk,
        'medium_risk': medium_risk,
        'low_risk': low_risk,
    }
    
    return render(request, 'reports.html', context)

@login_required(login_url='custom_login')
def download_attrition_employees(request):
    """Download CSV of employees at risk of attrition (is_retained=False)"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attrition_employees.csv"'
    
    writer = csv.writer(response)
    # CSV Headers
    writer.writerow([
        'Employee ID', 'Name', 'Age', 'Gender', 'Marital Status',
        'Job Satisfaction', 'Working Hours', 'Years at Company',
        'Distance From Home', 'Environment Satisfaction', 'Health Condition',
        'Expectations From Company', 'Joining Salary', 'Current Salary',
        'Education', 'Attrition Risk (%)', 'Data Source', 'Date Added'
    ])
    
    # Get attrition employees (is_retained=False)
    attrition_employees = EmployeeAttrition.objects.filter(is_retained=False).order_by('-attrition_probability')
    
    for employee in attrition_employees:
        writer.writerow([
            employee.employee_id,
            employee.name,
            employee.age,
            employee.gender,
            employee.marital_status,
            employee.job_satisfaction,
            employee.working_hours,
            employee.years_at_company,
            employee.distance_from_home,
            employee.environment_satisfaction,
            employee.health_condition,
            employee.expectations_from_company,
            employee.joining_salary,
            employee.current_salary,
            employee.education,
            f"{employee.attrition_probability:.1f}%",
            employee.data_source,
            employee.created_at.strftime('%Y-%m-%d %H:%M')
        ])
    
    return response

@login_required(login_url='custom_login')
def download_retention_employees(request):
    """Download CSV of employees likely to be retained (is_retained=True)"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="retention_employees.csv"'
    
    writer = csv.writer(response)
    # CSV Headers
    writer.writerow([
        'Employee ID', 'Name', 'Age', 'Gender', 'Marital Status',
        'Job Satisfaction', 'Working Hours', 'Years at Company',
        'Distance From Home', 'Environment Satisfaction', 'Health Condition',
        'Expectations From Company', 'Joining Salary', 'Current Salary',
        'Education', 'Attrition Risk (%)', 'Data Source', 'Date Added'
    ])
    
    # Get retention employees (is_retained=True)
    retention_employees = EmployeeAttrition.objects.filter(is_retained=True).order_by('attrition_probability')
    
    for employee in retention_employees:
        writer.writerow([
            employee.employee_id,
            employee.name,
            employee.age,
            employee.gender,
            employee.marital_status,
            employee.job_satisfaction,
            employee.working_hours,
            employee.years_at_company,
            employee.distance_from_home,
            employee.environment_satisfaction,
            employee.health_condition,
            employee.expectations_from_company,
            employee.joining_salary,
            employee.current_salary,
            employee.education,
            f"{employee.attrition_probability:.1f}%",
            employee.data_source,
            employee.created_at.strftime('%Y-%m-%d %H:%M')
        ])
    
    return response


@login_required(login_url='custom_login')
def president_dashboard(request):
    # Only active Presidents can access
    if not getattr(request.user, "is_active_president", False):
        return redirect('custom_login')

    subadmins = President.objects.filter(is_staff=True)

    if request.method == 'POST':
        form = SubAdminCreationForm(request.POST)
        if form.is_valid():
            subadmin = form.save(commit=False)
            subadmin.is_staff = True
            subadmin.save()
            return redirect('employee:president_dashboard')
    else:
        form = SubAdminCreationForm()

    context = {
        'subadmins': subadmins,
        'form': form
    }
    return render(request, 'president_dashboard.html', context)


# ❌ Do NOT require login
def feedback_form(request):
    success = False
    if request.method == "POST":
        post_data = request.POST.copy()
        post_data['data_source'] = 'Feedback Form'
        form = EmployeeAttritionForm(post_data)

        if form.is_valid():
            employee_data = {
                'Age': form.cleaned_data['age'],
                'Gender': form.cleaned_data['gender'],
                'MaritalStatus': form.cleaned_data['marital_status'],
                'JobSatisfaction': form.cleaned_data['job_satisfaction'],
                'WorkingHours': form.cleaned_data['working_hours'],
                'YearsAtCompany': form.cleaned_data['years_at_company'],
                'DistanceFromHome': form.cleaned_data['distance_from_home'],
                'EnvironmentSatisfaction': form.cleaned_data['environment_satisfaction'],
                'HealthCondition': form.cleaned_data['health_condition'],
                'ExpectationsFromCompany': form.cleaned_data['expectations_from_company'],
                'JoiningSalary': form.cleaned_data['joining_salary'],
                'CurrentSalary': form.cleaned_data['current_salary'],
                'Education': form.cleaned_data['education'],
            }

            attrition_pred, probability_pred = predictor.predict_single_employee(employee_data)
            employee = form.save(commit=False)
            employee.attrition = attrition_pred
            employee.attrition_probability = probability_pred
            employee.is_retained = probability_pred < 25
            employee.save()

            success = True
            form = EmployeeAttritionForm()

            risk_level = "High" if probability_pred >= 75 else "Medium" if probability_pred >= 50 else "Low"
            retention_status = "✅ RETAINED" if employee.is_retained else "⚠️ AT-RISK"

            messages.success(
                request,
                f"Employee data saved successfully! "
                f"Attrition Risk: {risk_level} ({probability_pred:.1f}%) - Status: {retention_status}"
            )
        else:
            print("Form errors:", form.errors)
    else:
        form = EmployeeAttritionForm()

    return render(request, "feedbackform.html", {
        "form": form,
        "success": success
    })


@login_required(login_url='custom_login')
def upload_csv(request):
    context = {
        "form": CSVUploadForm(),
        "employees": [],
        "low_risk_count": 0,
        "medium_risk_count": 0,
        "high_risk_count": 0,
        "retained_count": 0,
    }

    if request.method == "POST":
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']
            try:
                df = pd.read_csv(csv_file)

                feature_columns = [
                    'Age', 'Gender', 'MaritalStatus', 'JobSatisfaction', 'WorkingHours',
                    'YearsAtCompany', 'DistanceFromHome', 'EnvironmentSatisfaction',
                    'HealthCondition', 'ExpectationsFromCompany', 'JoiningSalary',
                    'CurrentSalary', 'Education'
                ]

                df_features = df[feature_columns].copy()
                attrition_predictions, attrition_probabilities = predictor.predict_attrition_bulk(df_features)

                uploaded_employees = []
                retained_count = 0

                for idx, row in df.iterrows():
                    probability = float(attrition_probabilities[idx])
                    is_retained = probability < 25
                    if is_retained:
                        retained_count += 1

                    employee_obj, created = EmployeeAttrition.objects.update_or_create(
                        employee_id=row['EmployeeID'],
                        defaults={
                            "name": row.get("Name", "Unknown"),
                            "age": row["Age"],
                            "gender": row["Gender"],
                            "marital_status": row["MaritalStatus"],
                            "job_satisfaction": row["JobSatisfaction"],
                            "working_hours": row["WorkingHours"],
                            "years_at_company": row["YearsAtCompany"],
                            "distance_from_home": row["DistanceFromHome"],
                            "environment_satisfaction": row["EnvironmentSatisfaction"],
                            "health_condition": row["HealthCondition"],
                            "expectations_from_company": row["ExpectationsFromCompany"],
                            "joining_salary": row["JoiningSalary"],
                            "current_salary": row["CurrentSalary"],
                            "education": row["Education"],
                            "attrition": int(attrition_predictions[idx]),
                            "attrition_probability": probability,
                            "is_retained": is_retained,
                            "data_source": "CSV",
                        }
                    )

                    employee_obj.attrition_probability = probability
                    uploaded_employees.append(employee_obj)

                low_risk_count = sum(1 for emp in uploaded_employees if emp.attrition_probability < 50)
                medium_risk_count = sum(1 for emp in uploaded_employees if 50 <= emp.attrition_probability < 75)
                high_risk_count = sum(1 for emp in uploaded_employees if emp.attrition_probability >= 75)

                messages.success(
                    request,
                    f"CSV uploaded successfully! {len(uploaded_employees)} employees processed with ML predictions. "
                    f"🟢 {retained_count} RETAINED (<25% risk) | "
                    f"Risk Distribution: {high_risk_count} High, {medium_risk_count} Medium, {low_risk_count} Low"
                )

                context.update({
                    "form": CSVUploadForm(),
                    "employees": uploaded_employees,
                    "low_risk_count": low_risk_count,
                    "medium_risk_count": medium_risk_count,
                    "high_risk_count": high_risk_count,
                    "retained_count": retained_count,
                })

            except Exception as e:
                messages.error(request, f"Error processing file: {e}")
                print(f"❌ CSV processing error: {e}")

    return render(request, "prediction.html", context)

@login_required(login_url='custom_login')
def dashboard(request):
    # Get all employees
    employees = EmployeeAttrition.objects.all()
    
    # Calculate statistics
    total_employees = employees.count()
    retained_employees = employees.filter(is_retained=True).count()
    attrition_employees = employees.filter(is_retained=False).count()
    
    # Risk categorization
    high_risk = employees.filter(attrition_probability__gte=75).count()
    medium_risk = employees.filter(attrition_probability__gte=50, attrition_probability__lt=75).count()
    low_risk = employees.filter(attrition_probability__lt=50).count()
    
    # Calculate percentages (avoid division by zero)
    if total_employees > 0:
        attrition_rate = round((attrition_employees / total_employees) * 100, 1)
        low_risk_percentage = round((low_risk / total_employees) * 100, 1)
        medium_risk_percentage = round((medium_risk / total_employees) * 100, 1)
        high_risk_percentage = round((high_risk / total_employees) * 100, 1)
    else:
        attrition_rate = 0
        low_risk_percentage = 0
        medium_risk_percentage = 0
        high_risk_percentage = 0
    
    context = {
        'total_employees': total_employees,
        'retained_employees': retained_employees,
        'attrition_employees': attrition_employees,
        'high_risk': high_risk,
        'medium_risk': medium_risk,
        'low_risk': low_risk,
        'attrition_rate': attrition_rate,
        'low_risk_percentage': low_risk_percentage,
        'medium_risk_percentage': medium_risk_percentage,
        'high_risk_percentage': high_risk_percentage,
    }
    
    return render(request, 'dashboard.html', context)
import json
from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q, Max, Min
from employee.models import EmployeeAttrition
from django.http import JsonResponse

@login_required(login_url='custom_login')
def analytics(request):
    """
    Comprehensive analytics view using existing EmployeeAttrition model fields
    """
    # Get time range filter from request
    time_range = request.GET.get('time_range', '30')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Base queryset
    employees = EmployeeAttrition.objects.all()
    
    # Apply time filtering
    if time_range and time_range != 'all':
        try:
            days = int(time_range)
            cutoff_date = timezone.now() - timedelta(days=days)
            employees = employees.filter(created_at__gte=cutoff_date)
        except (ValueError, TypeError):
            pass
    
    # Apply custom date range if provided
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            employees = employees.filter(created_at__gte=start, created_at__lte=end)
        except ValueError:
            pass
    
    # Basic Statistics
    total_employees = employees.count()
    retained_employees = employees.filter(is_retained=True).count()
    attrition_employees = employees.filter(is_retained=False).count()
    
    # Risk categorization
    high_risk = employees.filter(attrition_probability__gte=75).count()
    medium_risk = employees.filter(attrition_probability__gte=50, attrition_probability__lt=75).count()
    low_risk = employees.filter(attrition_probability__lt=50).count()
    
    # Calculate rates
    if total_employees > 0:
        attrition_rate = round((attrition_employees / total_employees) * 100, 1)
        retention_rate = round((retained_employees / total_employees) * 100, 1)
        avg_risk_score = employees.aggregate(Avg('attrition_probability'))['attrition_probability__avg'] or 0
        avg_risk_score = round(avg_risk_score, 1)
    else:
        attrition_rate = retention_rate = avg_risk_score = 0
    
    # Risk Distribution Data (for doughnut chart)
    risk_distribution = {
        'labels': ['Low Risk (0-49%)', 'Medium Risk (50-74%)', 'High Risk (75-100%)'],
        'data': [low_risk, medium_risk, high_risk]
    }
    
    # Gender Analysis (replacing department analysis)
    gender_data = get_gender_analysis(employees)
    
    # Job Satisfaction Analysis
    satisfaction_data = get_satisfaction_analysis(employees)
    
    # Monthly Trend Analysis (simulated based on created_at)
    trend_data = get_monthly_trend_analysis(employees)
    
    # Hiring vs Attrition (quarterly simulation)
    hiring_attrition_data = get_hiring_attrition_simulation()
    
    # Age Group Analysis
    age_group_data = get_age_group_analysis(employees)
    
    # Experience Level Analysis (years_at_company)
    experience_data = get_experience_analysis(employees)
    
    # Salary Distribution
    salary_distribution = get_salary_distribution(employees)
    
    # Risk Score Distribution
    risk_score_distribution = get_risk_score_distribution(employees)
    
    # Feature Importance (based on your actual model fields)
    feature_importance = get_feature_importance_data()
    
    context = {
        # Basic metrics
        'total_employees': total_employees,
        'retained_employees': retained_employees,
        'attrition_employees': attrition_employees,
        'high_risk': high_risk,
        'medium_risk': medium_risk,
        'low_risk': low_risk,
        'attrition_rate': attrition_rate,
        'retention_rate': retention_rate,
        'avg_risk_score': avg_risk_score,
        
        # Chart data (as JSON for JavaScript)
        'risk_distribution': json.dumps(risk_distribution),
        'gender_data': json.dumps(gender_data),  # Replacing department_data
        'satisfaction_data': json.dumps(satisfaction_data),
        'trend_data': json.dumps(trend_data),
        'hiring_attrition_data': json.dumps(hiring_attrition_data),
        'age_group_data': json.dumps(age_group_data),
        'experience_data': json.dumps(experience_data),
        'salary_distribution': json.dumps(salary_distribution),
        'risk_score_distribution': json.dumps(risk_score_distribution),
        'feature_importance': json.dumps(feature_importance),
        
        # Filter values
        'selected_time_range': time_range,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'analytics.html', context)


def get_gender_analysis(employees):
    """
    Analyze attrition by gender (replacing department analysis)
    """
    if employees.count() == 0:
        return {'labels': [], 'data': []}
    
    # Get gender distribution from attrition employees
    gender_counts = employees.filter(is_retained=False).values('gender').annotate(
        count=Count('id')
    ).order_by('gender')
    
    labels = []
    data = []
    
    for item in gender_counts:
        labels.append(item['gender'] or 'Not Specified')
        data.append(item['count'])
    
    # If no data, provide default structure
    if not labels:
        labels = ['Male', 'Female', 'Other']
        data = [0, 0, 0]
    
    return {
        'labels': labels,
        'data': data
    }


def get_satisfaction_analysis(employees):
    """
    Analyze satisfaction levels based on job_satisfaction field
    """
    if employees.count() == 0:
        return {'labels': [], 'data': []}
    
    # Aggregate by job_satisfaction levels (1-5 scale)
    satisfaction_counts = employees.values('job_satisfaction').annotate(
        count=Count('id')
    ).order_by('job_satisfaction')
    
    # Map satisfaction levels to descriptive labels
    satisfaction_labels = {
        1: 'Very Low',
        2: 'Low', 
        3: 'Medium',
        4: 'High',
        5: 'Very High'
    }
    
    # Initialize all levels with 0
    all_levels = ['Very Low', 'Low', 'Medium', 'High', 'Very High']
    complete_data = [0] * 5
    
    for item in satisfaction_counts:
        level = item['job_satisfaction']
        count = item['count']
        if 1 <= level <= 5:
            complete_data[level - 1] = count
    
    return {
        'labels': all_levels,
        'data': complete_data
    }


def get_monthly_trend_analysis(employees):
    """
    Get monthly attrition trends based on created_at field
    """
    if employees.count() == 0:
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        return {
            'labels': months,
            'attrition_rates': [0] * 12
        }
    
    # Get monthly employee counts for the past 12 months
    monthly_data = []
    months = []
    
    current_date = timezone.now()
    for i in range(12):
        # Calculate month start and end
        if i == 0:
            month_start = current_date.replace(day=1)
        else:
            if month_start.month == 1:
                month_start = month_start.replace(year=month_start.year - 1, month=12, day=1)
            else:
                month_start = month_start.replace(month=month_start.month - 1, day=1)
        
        # Calculate next month for end date
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1)
        
        # Count employees created in this month with high attrition risk
        month_count = employees.filter(
            created_at__gte=month_start,
            created_at__lt=month_end,
            attrition_probability__gte=50
        ).count()
        
        total_month = employees.filter(
            created_at__gte=month_start,
            created_at__lt=month_end
        ).count()
        
        # Calculate attrition rate for the month
        if total_month > 0:
            month_rate = round((month_count / total_month) * 100, 1)
        else:
            month_rate = 0
        
        months.insert(0, month_start.strftime('%b'))
        monthly_data.insert(0, month_rate)
    
    return {
        'labels': months,
        'attrition_rates': monthly_data
    }


def get_hiring_attrition_simulation():
    """
    Simulated quarterly hiring vs attrition data
    """
    return {
        'labels': ['Q1 2024', 'Q2 2024', 'Q3 2024', 'Q4 2024'],
        'hiring': [45, 52, 38, 41],
        'attrition': [28, 35, 22, 31]
    }


def get_age_group_analysis(employees):
    """
    Analyze attrition by age groups using existing age field
    """
    if employees.count() == 0:
        return {'labels': [], 'data': []}
    
    # Define age ranges and count high-risk employees in each
    age_groups = {
        '22-30': employees.filter(age__gte=22, age__lte=30, attrition_probability__gte=50).count(),
        '31-40': employees.filter(age__gte=31, age__lte=40, attrition_probability__gte=50).count(),
        '41-50': employees.filter(age__gte=41, age__lte=50, attrition_probability__gte=50).count(),
        '51-60': employees.filter(age__gte=51, age__lte=60, attrition_probability__gte=50).count(),
        '60+': employees.filter(age__gt=60, attrition_probability__gte=50).count(),
    }
    
    return {
        'labels': list(age_groups.keys()),
        'data': list(age_groups.values())
    }


def get_experience_analysis(employees):
    """
    Analyze attrition by years of experience using years_at_company
    """
    if employees.count() == 0:
        return {'labels': [], 'data': []}
    
    # Group by years at company
    experience_groups = {
        '0-2 years': employees.filter(years_at_company__gte=0, years_at_company__lte=2, attrition_probability__gte=50).count(),
        '3-5 years': employees.filter(years_at_company__gte=3, years_at_company__lte=5, attrition_probability__gte=50).count(),
        '6-10 years': employees.filter(years_at_company__gte=6, years_at_company__lte=10, attrition_probability__gte=50).count(),
        '11-15 years': employees.filter(years_at_company__gte=11, years_at_company__lte=15, attrition_probability__gte=50).count(),
        '15+ years': employees.filter(years_at_company__gt=15, attrition_probability__gte=50).count(),
    }
    
    return {
        'labels': list(experience_groups.keys()),
        'data': list(experience_groups.values())
    }


def get_salary_distribution(employees):
    """
    Get salary distribution using current_salary field
    """
    if employees.count() == 0:
        return {'labels': [], 'data': []}
    
    # Get min and max salary to create dynamic ranges
    salary_stats = employees.aggregate(
        min_salary=Min('current_salary'),
        max_salary=Max('current_salary')
    )
    
    min_sal = salary_stats['min_salary'] or 30000
    max_sal = salary_stats['max_salary'] or 100000
    
    # Create salary ranges based on actual data
    ranges = []
    range_size = (max_sal - min_sal) / 7  # 7 ranges
    
    for i in range(7):
        range_start = int(min_sal + (i * range_size))
        range_end = int(min_sal + ((i + 1) * range_size))
        
        if i == 6:  # Last range
            count = employees.filter(current_salary__gte=range_start).count()
            label = f'{range_start//1000}K+'
        else:
            count = employees.filter(current_salary__gte=range_start, current_salary__lt=range_end).count()
            label = f'{range_start//1000}-{range_end//1000}K'
        
        ranges.append({
            'label': label,
            'count': count
        })
    
    return {
        'labels': [r['label'] for r in ranges],
        'data': [r['count'] for r in ranges]
    }


def get_risk_score_distribution(employees):
    """
    Get risk score distribution using attrition_probability field
    """
    if employees.count() == 0:
        return {'labels': [], 'data': []}
    
    # Define risk score ranges
    risk_ranges = {}
    labels = []
    
    for i in range(0, 100, 10):
        range_label = f'{i}-{i+10}%'
        labels.append(range_label)
        
        if i == 90:  # Last range
            count = employees.filter(attrition_probability__gte=i).count()
        else:
            count = employees.filter(
                attrition_probability__gte=i, 
                attrition_probability__lt=i+10
            ).count()
        
        risk_ranges[range_label] = count
    
    return {
        'labels': labels,
        'data': list(risk_ranges.values())
    }


def get_feature_importance_data():
    """
    Feature importance based on your actual EmployeeAttrition model fields
    """
    return {
        'labels': [
            'Job Satisfaction',
            'Working Hours',
            'Environment Satisfaction', 
            'Distance From Home',
            'Current Salary',
            'Health Condition',
            'Years at Company',
            'Age',
            'Education Level',
            'Marital Status'
        ],
        'importance_scores': [0.45, 0.32, 0.28, 0.22, 0.18, 0.15, 0.12, 0.10, 0.08, 0.05]
    }


@login_required(login_url='custom_login')
def analytics_api(request):
    """
    API endpoint for dynamic chart updates via AJAX
    """
    if request.method == 'GET':
        time_range = request.GET.get('time_range', '30')
        chart_type = request.GET.get('chart_type', 'all')
        
        # Apply filters
        employees = EmployeeAttrition.objects.all()
        if time_range != 'all':
            try:
                days = int(time_range)
                cutoff_date = timezone.now() - timedelta(days=days)
                employees = employees.filter(created_at__gte=cutoff_date)
            except (ValueError, TypeError):
                pass
        
        # Return updated data
        data = {}
        
        if chart_type == 'risk_distribution' or chart_type == 'all':
            high_risk = employees.filter(attrition_probability__gte=75).count()
            medium_risk = employees.filter(attrition_probability__gte=50, attrition_probability__lt=75).count()
            low_risk = employees.filter(attrition_probability__lt=50).count()
            
            data['risk_distribution'] = {
                'labels': ['Low Risk', 'Medium Risk', 'High Risk'],
                'data': [low_risk, medium_risk, high_risk]
            }
        
        if chart_type == 'satisfaction' or chart_type == 'all':
            data['satisfaction_data'] = get_satisfaction_analysis(employees)
        
        return JsonResponse(data)
