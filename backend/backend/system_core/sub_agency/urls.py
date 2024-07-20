from django.urls import path
from .views import SubAgencyDashboardView, SubAgencyChannelView, SubAgencyReportView, SubAgencyTransactionView, \
    SubAgencySettingsView, SubAgencyServiceView, SubAgencyGetServiceInformation

app_name = "sub-agency"

urlpatterns = [
    path("dashboard", SubAgencyDashboardView.as_view(), name="sub-agency-dashboard"),
    path("channels", SubAgencyChannelView.as_view(), name="sub-agency-channel"),
    path("reports", SubAgencyReportView.as_view(), name="sub-agency-report"),
    path("transactions", SubAgencyTransactionView.as_view(), name="sub-agency-transaction"),
    path("services", SubAgencyServiceView.as_view(), name="services"),
    path("get-service-info/<int:pk>", SubAgencyGetServiceInformation.as_view(), name="get-service-info"),
    path("settings", SubAgencySettingsView.as_view(), name="sub-agency-setting"),
]
