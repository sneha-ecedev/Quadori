from django.urls import path

from . import views

app_name = 'movie'

urlpatterns = [
    path('', views.search_movies, name='search'),
    path('book/', views.book_movie, name='book'),
    path('confirmation/<uuid:booking_id>/', views.booking_confirmation, name='confirmation'),
]
