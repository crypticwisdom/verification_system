from django.urls import path
from . import views

app_name = "business"

urlpatterns = [
    path('dashboard', views.BDashboardView.as_view(), name="dashboard"),
    path('verifications', views.BVerificationView.as_view(), name="verifications"),
    path('verification/<int:pk>', views.BVerificationView.as_view(), name="verifications"),
    path('transactions', views.BTransactionView.as_view(), name="transactions"),
    path('get-service-info/<int:pk>', views.BGetServiceInformation.as_view(), name="get-service-info"),
    path('settings', views.BusinessSettingsView.as_view(), name="business-settings"),
    path('get-profile', views.BusinessSettingsView.as_view(), name="get-individual-profile"),
]
