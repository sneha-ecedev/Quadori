from django.urls import path

from . import views

app_name = 'mybookings'

urlpatterns = [
    path('', views.booking_list, name='list'),
    path('ticket/<str:service_key>/<uuid:booking_id>/', views.download_ticket, name='ticket'),
    path('<str:service_key>/<uuid:booking_id>/cancel/', views.cancel_booking, name='cancel'),
]
