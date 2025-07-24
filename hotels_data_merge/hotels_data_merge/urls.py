from django.urls import path
from . import views

urlpatterns = [
    path('hotels', views.hotels_api, name='hotels_api'),
]