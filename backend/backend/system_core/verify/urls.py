from django.urls import path
from verify import views

app_name = "verify"

urlpatterns = [
    path('web/', views.IWebProcessorView.as_view(), name="dashboard"),
    path('confirm-transaction/', views.VerifyTransactionView.as_view(), name="confirm-transaction"),
]
