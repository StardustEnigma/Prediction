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
