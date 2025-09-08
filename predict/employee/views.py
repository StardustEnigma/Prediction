# views.py
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from employee.models import President
from .forms import EmployeeAttritionForm, CSVUploadForm, SubAdminCreationForm
from .models import EmployeeAttrition
from .ml_utils import predictor


@login_required
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


def feedback_form(request):
    success = False

    if request.method == "POST":
        # Make a mutable copy of POST data
        post_data = request.POST.copy()
        post_data['data_source'] = 'Feedback Form'

        form = EmployeeAttritionForm(post_data)

        if form.is_valid():
            # Get cleaned form data for ML prediction
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
            
            # ✅ Use ML model to predict attrition
            attrition_pred, probability_pred = predictor.predict_single_employee(employee_data)
            
            # Save form with ALL ML predictions
            employee = form.save(commit=False)
            employee.attrition = attrition_pred  # ✅ ML prediction (0 or 1)
            employee.attrition_probability = probability_pred  # ✅ NEW: Risk percentage
            employee.is_retained = probability_pred < 25  # ✅ NEW: Retention flag
            employee.save()
            
            success = True
            form = EmployeeAttritionForm()  # Reset form after saving
            
            # Enhanced success message with retention status
            risk_level = "High" if probability_pred >= 75 else "Medium" if probability_pred >= 50 else "Low"
            retention_status = "✅ RETAINED" if employee.is_retained else "⚠️ AT-RISK"
            
            messages.success(
                request, 
                f"Employee data saved successfully! "
                f"Attrition Risk: {risk_level} ({probability_pred:.1f}%) - Status: {retention_status}"
            )
            
            print(f"✅ Employee saved: Attrition={attrition_pred}, Probability={probability_pred:.1f}%, Retained={employee.is_retained}")
        else:
            print("Form errors:", form.errors)

    else:
        form = EmployeeAttritionForm()

    return render(request, "feedbackform.html", {
        "form": form,
        "success": success
    })


def upload_csv(request):
    # Initialize empty context for GET requests (page loads/refreshes)
    context = {
        "form": CSVUploadForm(),
        "employees": [],
        "low_risk_count": 0,
        "medium_risk_count": 0,
        "high_risk_count": 0,
        "retained_count": 0,  # ✅ NEW: Add retained count
    }
    
    if request.method == "POST":
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']
            try:
                # Read CSV into DataFrame
                df = pd.read_csv(csv_file)
                
                # Prepare data for ML prediction
                feature_columns = [
                    'Age', 'Gender', 'MaritalStatus', 'JobSatisfaction', 'WorkingHours', 
                    'YearsAtCompany', 'DistanceFromHome', 'EnvironmentSatisfaction', 
                    'HealthCondition', 'ExpectationsFromCompany', 'JoiningSalary', 
                    'CurrentSalary', 'Education'
                ]
                
                # Create DataFrame with feature columns for prediction
                df_features = df[feature_columns].copy()
                
                # ✅ Use ML model to predict attrition for all employees
                attrition_predictions, attrition_probabilities = predictor.predict_attrition_bulk(df_features)
                
                uploaded_employees = []
                retained_count = 0  # ✅ NEW: Count retained employees
                
                # Loop through rows and save to database
                for idx, row in df.iterrows():
                    probability = float(attrition_probabilities[idx])
                    is_retained = probability < 25  # ✅ NEW: Calculate retention status
                    
                    # Count retained employees
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
                            "attrition": int(attrition_predictions[idx]),  # ✅ ML prediction
                            "attrition_probability": probability,  # ✅ NEW: Store risk percentage
                            "is_retained": is_retained,  # ✅ NEW: Store retention status
                            "data_source": "CSV",
                        }
                    )
                    
                    # ✅ Add ML-predicted probability for display
                    employee_obj.attrition_probability = probability
                    uploaded_employees.append(employee_obj)
                
                # Calculate risk counts based on ML predictions
                low_risk_count = sum(1 for emp in uploaded_employees if emp.attrition_probability < 50)
                medium_risk_count = sum(1 for emp in uploaded_employees if 50 <= emp.attrition_probability < 75)
                high_risk_count = sum(1 for emp in uploaded_employees if emp.attrition_probability >= 75)
                
                # ✅ Enhanced success message with retention info
                messages.success(
                    request, 
                    f"CSV uploaded successfully! {len(uploaded_employees)} employees processed with ML predictions. "
                    f"🟢 {retained_count} RETAINED (<25% risk) | "
                    f"Risk Distribution: {high_risk_count} High, {medium_risk_count} Medium, {low_risk_count} Low"
                )
                
                # Update context to show data ONLY after successful upload
                context.update({
                    "form": CSVUploadForm(),  # Reset form
                    "employees": uploaded_employees,  # Show uploaded data with ML predictions
                    "low_risk_count": low_risk_count,
                    "medium_risk_count": medium_risk_count,
                    "high_risk_count": high_risk_count,
                    "retained_count": retained_count,  # ✅ NEW: Pass retained count
                })
                
                print(f"✅ CSV processed: {len(uploaded_employees)} employees, {retained_count} retained")
                
            except Exception as e:
                messages.error(request, f"Error processing file: {e}")
                print(f"❌ CSV processing error: {e}")
    
    return render(request, "prediction.html", context)
