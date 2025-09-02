from django.shortcuts import render

from django.shortcuts import render
from .forms import EmployeeAttritionForm

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
