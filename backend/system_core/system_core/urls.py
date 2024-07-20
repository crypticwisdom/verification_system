from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from account.views import service_welcome, StatesCRView

urlpatterns = [
    path('', service_welcome, name="welcome_page"),
    path('states', StatesCRView.as_view(), name="states"),
    path('admin/', admin.site.urls),
    path('account/', include('account.urls')),
    path('platform/', include('super_admin.urls', 'partner_manager.urls')),  # super-admin/
    path('platform/pm/', include('partner_manager.urls')),  # platform/pm/agency/
    path('individual/', include('individual.urls')),  # /individual/
    path('business/', include('business.urls')),  # /business/
    path('verify/', include('verify.urls')),  # /verify/
    path('agency/', include('agencies.urls')),  # /agency/
    path('sub-agency/', include('sub_agency.urls')),  # /sub-agency/
    path('developer/', include('developer.urls')),  # /sub-agency/
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
