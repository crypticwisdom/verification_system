from django.urls import path
from . import views

app_name = "super_admin"

urlpatterns = [
    path('user-category/', views.SuperAdminUserCategoryDashboardView.as_view(), name="user-category"),
    path('user/', views.SuperAdminUserOperationView.as_view(), name="user"),  # R,U, individual user detail
    path('user/<int:pk>', views.SuperAdminUserOperationView.as_view(), name="user-detail"),  # R,U, individual user detail
    path('category', views.SuperAdminUserEachCategoriesView.as_view(), name="each-category"), # Get each category ?category=agency
    path('create-user/', views.SuperAdminCreateUsersView.as_view(), name="create-user"),

    # View individual agency.
    path('category/agency/<int:pk>', views.SuperAdminIndividualAgencyView.as_view(), name="get-agency"),

    # Handles Service get, put, delete, post ...
    path('service', views.SuperAdminCreateNewServiceView.as_view(), name="service"),

    # Add new service to agency profile; Activate Service status.
    path('add-service', views.SuperAdminAddServiceView.as_view(), name="add-service"),
    path('activate-service', views.SuperAdminAddServiceView.as_view(), name="activate-service"),
    path('existing-services/<int:agencyId>', views.SuperAdminAddServiceView.as_view(), name="existing-and-non-existing-services"),  # Fetches all serviceDetail for adding serviceDetail to Agency

    path('service/<int:pk>/', views.SuperAdminCreateNewServiceView.as_view(), name="get-service"),  # GET
    path('service/<int:pk>/', views.SuperAdminCreateNewServiceView.as_view(), name="delete-service"),  # DELETE

    # Transaction
    path('transaction', views.SuperAdminTransactionView.as_view(), name="transaction"),

    # Channel
    path('channel', views.SuperAdminChannelView.as_view(), name="fetch-channels"),  # GET
    path('create-channel/', views.SuperAdminChannelView.as_view(), name="create-channels"),  # POST

    # Get list of all agencies including the once already 'related' to the PartnerManager
    path('related-agencies', views.SuperAdminAssignAgencyView.as_view(), name="list-related-agencies"),  # GET

    # Dashboard
    path('dashboard', views.SuperAdminDashboardView.as_view(), name="dashboard"),  # GET

    # Break Down
    path('break-down', views.DashboardBreakDownOfRevenueView.as_view(), name="break-down"),  # GET

    # Report
    path('report', views.SuperAdminReportView.as_view(), name="reports"),  # GET

    # Create payment gateway
    path('create/payment-gateway', views.SuperAdminCreatePaymentGateWayView.as_view(), name="create-payment-gateway"),  # POST

]
