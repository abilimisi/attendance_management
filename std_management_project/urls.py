from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from std_management_app.views import home_view # Import the home view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('teacher/', include('std_management_app.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)