from django.urls import path
from partner_manager import views


app_name = "partner-manager"

urlpatterns = [
    path("dashboard", views.PMDashBoardView.as_view(), name="pm-dashboard"),
    path("agency", views.PMAgencyView.as_view(), name="pm-agency"),
    path("agency/<int:pk>", views.PMAgencyView.as_view(), name="pm-agency-detail"),
    path("channels", views.PMChannelView.as_view(), name="pm-channels"),
    path("reports", views.PMReportView.as_view(), name="pm-channels"),
    path("transactions", views.PMTransactionView.as_view(), name="pm-transaction"),
]
