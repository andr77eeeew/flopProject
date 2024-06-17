from django.urls import path
from floplegends import views

urlpatterns = [
    path('create/', views.CreateflopLegendsView.as_view(), name='create'),
    path('all/', views.AllflopLegendsView.as_view(), name='all'),
]