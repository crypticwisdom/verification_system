from django.contrib import admin
from .models import User, UserDetail, UserRole, State, Service, ServiceDetail, Transaction, Channel, PaymentGateWay, ClientPaymentGateWayDetail

# Register your models here.

admin.site.register(User)
admin.site.register(UserDetail)
admin.site.register(UserRole)
admin.site.register(State)
admin.site.register(Service)
admin.site.register(ServiceDetail)
admin.site.register(PaymentGateWay)
admin.site.register(ClientPaymentGateWayDetail)
admin.site.register(Transaction)
admin.site.register(Channel)

