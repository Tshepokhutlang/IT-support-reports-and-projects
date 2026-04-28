from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('tickets/', views.ticket_list, name='ticket_list'),
    path('tickets/new/', views.ticket_create, name='ticket_create'),
    path('tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
]