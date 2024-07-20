from django.urls import path
from agencies import views

app_name = "agency"

urlpatterns = [
    path("dashboard", views.AgencyDashboardView.as_view(), name="agency-dash"),
    path("sub-agencies", views.AgencySubAgenciesView.as_view(), name="sub-agencies"),
    path("get/sub-agency/<int:pk>", views.AgencyGetSubAgencyProfileView.as_view(), name="get-agency"),
    path("channels", views.AgencyChannelView.as_view(), name="channel"),
    path("create-agency", views.AgencyCreateSubAgencyView.as_view(), name="create-agency"),
    path("list-services", views.AgencyCreateSubAgencyView.as_view(), name="list-services"),
    path("existing-services/<int:sub_agency_id>", views.AgencyExistingAndNonExistingServiceView.as_view(), name="existing-services"),  # GET
    path("add-service", views.AgencyExistingAndNonExistingServiceView.as_view(), name="add-service"),  # POST
    path("transactions", views.AgencyTransactionView.as_view(), name="get-transactions"),
    path("reports", views.AgencyReportView.as_view(), name="reports"),
]

