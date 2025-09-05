from django.urls import path
from . import views 
app_name = 'employee'
urlpatterns = [
   path('feedback/' , views.feedback_form,name='feedback'),
   path('dashboard/', views.president_dashboard, name='president_dashboard'),
   path("upload-csv/", views.upload_csv, name="upload_csv")
]