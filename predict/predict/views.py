from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages  

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
