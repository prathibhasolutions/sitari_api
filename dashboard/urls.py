from django.urls import path
from .views import dashboard_home, chat_view

urlpatterns = [
    path('', dashboard_home, name='dashboard-home'),
    path('chat/<int:customer_id>/', chat_view, name='dashboard-chat'),
]
