from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Lara Tours — Proposal Studio"
admin.site.site_title = "Lara Proposal Studio"
admin.site.index_title = "Manage catalog & proposals"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("proposals.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
