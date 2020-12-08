from django.urls import path, re_path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('',views.index, name='index'),
    # path('individuals/', views.IndividualsListView.as_view(),name='individuals'),
    # path('individual/<str:pk>', views.IndividualDetailView.as_view(), name='individual-detail'),
    # path('entities/', views.EntitiesListView.as_view(),name='entities'),
    # path('entity/<str:pk>', views.EntityDetailView.as_view(), name='entity-detail'),
    path('list/<str:list_name>/', views.list, name='list'),
    path('search/', views.search, name='search')
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
