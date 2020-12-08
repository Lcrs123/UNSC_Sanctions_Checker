from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('',views.index, name='index'),
    path('list/<str:list_name>/', views.list, name='list'),
    path('search/', views.search, name='search'),
    path('save_report', views.save_report, name='save_report'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
