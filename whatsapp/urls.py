from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'customers', views.CustomerViewSet, basename='customer')
router.register(r'messages', views.MessageViewSet, basename='message')
router.register(r'templates', views.TemplateViewSet, basename='template')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/', views.WhatsAppWebhookView.as_view(), name='whatsapp-webhook'),
    path('debug/', views.DebugConfigView.as_view(), name='debug-config'),
]
