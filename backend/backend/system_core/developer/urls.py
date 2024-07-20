from django.urls import path
from developer import views

app_name = "developer"

urlpatterns = [
    path('dashboard', views.DeveloperDashboardView.as_view(), name="developer-dashboard"),
]

