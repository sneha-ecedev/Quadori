from django.urls import path

from . import views

app_name = 'bus'

urlpatterns = [
    path('', views.search_buses, name='search'),
    path('book/', views.book_bus, name='book'),
    path('confirmation/<uuid:booking_id>/', views.booking_confirmation, name='confirmation'),
]
