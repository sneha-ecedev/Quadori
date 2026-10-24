from django.urls import path

from . import views

app_name = 'flight'

urlpatterns = [
    path('', views.search_flights, name='search'),
    path('passengers/', views.passenger_details, name='passengers'),
    path('confirmation/<uuid:booking_id>/', views.booking_confirmation, name='confirmation'),
]
