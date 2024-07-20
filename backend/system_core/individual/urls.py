from django.urls import path
from individual import views


app_name = "individual"

urlpatterns = [
    path('dashboard', views.IDashboardView.as_view(), name="dashboard"),
    path('verifications', views.IVerificationView.as_view(), name="verifications"),
    path('verification/<int:pk>', views.IVerificationView.as_view(), name="verifications"),
    path('transactions', views.ITransactionView.as_view(), name="transactions"),
    path('get-service-info/<int:pk>', views.IGetServiceInformation.as_view(), name="get-service-info"),
    path('settings', views.IndividualSettingsView.as_view(), name="individual-settings"),
    path('get-profile', views.IndividualSettingsView.as_view(), name="get-individual-profile"),
]
