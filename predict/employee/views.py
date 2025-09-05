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

def feedback_form(request):
    success = False  # flag for success message

    if request.method == "POST":
        form = EmployeeAttritionForm(request.POST)
        if form.is_valid():
            form.save()  # save data to DB
            success = True
            form = EmployeeAttritionForm()  # reset form after saving
    else:
        form = EmployeeAttritionForm()

    return render(request, "feedbackform.html", {"form": form, "success": success})
