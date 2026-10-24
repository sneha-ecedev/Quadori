from django.urls import path

from . import views

app_name = 'train'

urlpatterns = [
    path('', views.search_trains, name='search'),
    path('book/', views.book_train, name='book'),
    path('confirmation/<uuid:booking_id>/', views.booking_confirmation, name='confirmation'),
]
