from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('clinical_core.urls')),
]

handler403 = 'clinical_core.views.custom_permission_denied'
