from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from accounts.views import ManualTransaction


urlpatterns = [
    path("admin/accounts/enrollment/<int:enrollment_id>/change/transaction/", ManualTransaction),
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("api/schema", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs", SpectacularSwaggerView.as_view(url_name="schema"))
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
