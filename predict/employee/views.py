from django.shortcuts import render

from django.shortcuts import render
from .forms import EmployeeAttritionForm
# views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from employee.models import President

from .forms import SubAdminCreationForm

@login_required
@login_required
def president_dashboard(request):
    # Only active Presidents can access
    if not getattr(request.user, "is_active_president", False):
        return redirect('custom_login')  # make sure this URL exists

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
from django.shortcuts import render
from .forms import EmployeeAttritionForm

from django.shortcuts import render
from .forms import EmployeeAttritionForm

def feedback_form(request):
    success = False  # flag to show success message

    if request.method == "POST":
        # Make a mutable copy of POST data
        post_data = request.POST.copy()
        post_data['data_source'] = 'Feedback Form'  # set automatically

        print("POST data received (with data_source):", post_data)

        form = EmployeeAttritionForm(post_data)

        print("Form is_bound:", form.is_bound)
        print("Form is_valid before saving:", form.is_valid())

        if form.is_valid():
            form.save()  # save to database
            success = True
            form = EmployeeAttritionForm()  # reset form after saving
            print("Form saved successfully!")
        else:
            print("Form errors:", form.errors)

    else:
        form = EmployeeAttritionForm()

    return render(request, "feedbackform.html", {
        "form": form,
        "success": success
    })

import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CSVUploadForm
from .models import EmployeeAttrition

def upload_csv(request):
    if request.method == "POST":
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']
            try:
                # Read CSV into DataFrame
                df = pd.read_csv(csv_file)

                # Loop through rows and save
                for _, row in df.iterrows():
                    EmployeeAttrition.objects.update_or_create(
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
                            "attrition": row["Attrition"],
                            "data_source": "CSV",
                        }
                    )
                messages.success(request, "CSV uploaded and data saved successfully!")
                return redirect("employee:upload_csv")

            except Exception as e:
                messages.error(request, f"Error processing file: {e}")

    else:
        form = CSVUploadForm()

    return render(request, "prediction.html", {"form": form})
