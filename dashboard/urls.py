from django.urls import path
from .views import (
    portal_view, agent_login_view, admin_login_view, logout_view,
    dashboard_home, chat_view, chat_messages_api, privacy_view, terms_view,
    assign_chat
)

urlpatterns = [
    path('', portal_view, name='portal'),
    path('agent-login/', agent_login_view, name='agent-login'),
    path('admin-login/', admin_login_view, name='admin-login'),
    path('logout/', logout_view, name='logout'),
    path('home/', dashboard_home, name='dashboard-home'),
    path('chat/<int:customer_id>/', chat_view, name='dashboard-chat'),
    path('chat/<int:customer_id>/messages/', chat_messages_api, name='dashboard-chat-messages'),
    path('chat/<int:customer_id>/assign/', assign_chat, name='assign-chat'),
    path('privacy/', privacy_view, name='privacy'),
    path('terms/', terms_view, name='terms'),
]
