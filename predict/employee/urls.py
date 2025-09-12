from django.urls import path
from . import views 
from predict.views import custom_login
app_name = 'employee'
urlpatterns = [
   path('feedback/' , views.feedback_form,name='feedback'),
   path('pdashboard/', views.president_dashboard, name='president_dashboard'),
   path("prediction/", views.upload_csv, name="upload_csv"),
   path("login/", custom_login, name="custom_login"),
   path('reports/', views.reports, name='reports'),
    path('download-attrition/', views.download_attrition_employees, name='download_attrition_employees'),
    path('download-retention/', views.download_retention_employees, name='download_retention_employees'),
    path('dashboard/',views.dashboard,name='dashboard'),
    path('analytics/', views.analytics, name='analytics'),
    path('analytics/api/', views.analytics_api, name='analytics_api'),
]
