from django.urls import path

from . import views

app_name = 'restaurant'

urlpatterns = [
    path('', views.search_restaurants, name='search'),
    path('reserve/', views.reserve_table, name='reserve'),
    path('confirmation/<uuid:booking_id>/', views.booking_confirmation, name='confirmation'),
]
