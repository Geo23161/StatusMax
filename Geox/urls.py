"""
URL configuration for Geox project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView)
from django.urls.conf import include
from app.views import handle_click, index, privacy, delete_view, gamify_interest, download_page
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path('token/', TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path('token/refresh/', TokenRefreshView.as_view(), name="token_refresh"),
    path("api/", include('app.urls')),
    path('p/<int:id>/', handle_click, name="handle_clicks"),
    path('', index, name="index"),
    path('privacy/', privacy, name='privacy'),
    path('delete/', delete_view, name="delete_story"),
    path('g/<int:pk>/', gamify_interest, name="gamify_interest"),
    path('download/<int:pk>/', download_page, name = "download_page")
]+ static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)