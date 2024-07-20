from django.urls import path
from account import views
app_name = "account"

urlpatterns = [
    path('login', views.SignInView.as_view(), name="generic_login"),
    path('sign-up', views.AccountCreationView.as_view(), name="account-creation"),
    path('verify-business-cac', views.VerifyCACView.as_view(), name="verify-business-cac"),

    path('list-users', views.ListUsersView.as_view(), name="list-users"),
    path('list-services', views.LandPageListServicesView.as_view(), name="list-services"),
    path('list-service-details', views.ListServiceDetailView.as_view(), name="service-details"),
    path('channels', views.AllChannelsView.as_view(), name="channels"),
    path('check-data', views.MakeCheckFieldsView.as_view(), name="check-data"),
    path('all-types', views.AllUserRolesView.as_view(), name="all-types"),

    path('password-reset/<slug:slug>', views.GeneratedPasswordResetView.as_view(), name="password-reset"),
    path('forgot-password', views.ForgotPasswordView.as_view(), name="forgot-password"),

    path('verify/<slug:slug>', views.VerifyAccountView.as_view(), name="verify-account"),

    # All links related to Payments
    path('payment/banks', views.GetListOfBanksView.as_view(), name="banks"),
    path('payment/account-resolution', views.AccountResolutionView.as_view(), name="account-resolution"),
    path('payment/create-sub-account', views.GetListOfBanksView.as_view(), name="banks"),

    # Payment Gateway
    path('list/payment-gateways', views.PaymentGateWayOptions.as_view(), name="list-payment-gateways"),
]
