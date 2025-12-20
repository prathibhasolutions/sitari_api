from django.urls import path
from .views import dashboard_home, chat_view, chat_messages_api, privacy_view, terms_view

urlpatterns = [
    path('', dashboard_home, name='dashboard-home'),
    path('chat/<int:customer_id>/', chat_view, name='dashboard-chat'),
    path('chat/<int:customer_id>/messages/', chat_messages_api, name='dashboard-chat-messages'),
    path('privacy/', privacy_view, name='privacy'),
    path('terms/', terms_view, name='terms'),
]
