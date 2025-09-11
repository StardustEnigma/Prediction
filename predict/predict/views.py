from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages  
from django.contrib.auth.decorators import login_required
def custom_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")  
        else:
            messages.error(request, "Invalid username or password")  
            return redirect("custom_login")

    return render(request, "login.html")

def home(request):
    return render(request, "base.html")

def dash(request):
    return render(request, "dashboard.html")

def custom_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("custom_login")
def president_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        # Check if user exists AND is a President
        if user is not None and getattr(user, 'is_active_president', False):
            login(request, user)
            return redirect('employee:president_dashboard')  # president dashboard
        else:
            error = "Invalid credentials or you are not a President."
            return render(request, 'plogin.html', {'error': error})  # <-- use plogin.html

    return render(request, 'plogin.html')  # <-- use plogin.html consistently

    # <-- uses your login.html
@login_required
def president_logout(request):
    logout(request)
    return redirect('president_login')

from django.shortcuts import render
from django.views.decorators.cache import cache_page

def features_view(request):
    """
    Display the features landing page with ML Analytics platform capabilities.
    """
    context = {
        'page_title': 'Features - ML Analytics Platform',
        'meta_description': 'Discover powerful machine learning features for employee retention prediction and HR analytics.',
    }
    return render(request, 'features.html', context)


@cache_page(60 * 60)
def cached_features_view(request):
    """
    Cached version of features page for better performance.
    """
    context = {
        'page_title': 'Features - ML Analytics Platform',
        'meta_description': 'Discover powerful machine learning features for employee retention prediction and HR analytics.',
    }
    return render(request, 'features.html', context)
