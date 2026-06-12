# project/urls.py
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import path
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # TÜM app rotaları core.urls'te
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # WhiteNoise static dosyaları servis eder; media’yı biz servis edeceğiz
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]
