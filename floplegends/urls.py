from django.urls import path
from floplegends import views

urlpatterns = [
    path('create/', views.CreateflopLegendsView.as_view(), name='create'),
    path('update/<int:id>/', views.UpdateflopLegendsView.as_view(), name='update'),
    path('delete/<int:id>/', views.DeleteflopLegendsView.as_view(), name='delete'),
    path('all/', views.AllflopLegendsView.as_view(), name='all'),
]