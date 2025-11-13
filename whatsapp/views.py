from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Customer, Message, Template

from .serializers import CustomerSerializer, MessageSerializer, TemplateSerializer
from .whatsapp_api import send_whatsapp_message
from rest_framework.decorators import action

class CustomerViewSet(viewsets.ModelViewSet):
	queryset = Customer.objects.all()
	serializer_class = CustomerSerializer


class MessageViewSet(viewsets.ModelViewSet):
	queryset = Message.objects.all().select_related('customer', 'template')
	serializer_class = MessageSerializer

	@action(detail=False, methods=['post'], url_path='send-whatsapp')
	def send_whatsapp(self, request):
		to_number = request.data.get('to')
		template_name = request.data.get('template', 'hello_world')
		if not to_number:
			return Response({'error': 'Recipient number (to) is required.'}, status=400)
		api_response = send_whatsapp_message(to_number, template_name)
		return Response(api_response)

	def create(self, request, *args, **kwargs):
		# Optionally send WhatsApp message when creating a Message object
		response = super().create(request, *args, **kwargs)
		# You can trigger send_whatsapp_message here if needed
		return response

class TemplateViewSet(viewsets.ModelViewSet):
	queryset = Template.objects.all()
	serializer_class = TemplateSerializer

class WhatsAppWebhookView(APIView):
	VERIFY_TOKEN = "mywhatsappverify124"  # Set this to your chosen verify token

	def get(self, request, *args, **kwargs):
		import logging
		logger = logging.getLogger("whatsapp.webhook")
		logger.info(f"All GET params: {dict(request.GET)}")
		verify_token = request.GET.get('hub.verify_token')
		challenge = request.GET.get('hub.challenge')
		mode = request.GET.get('hub.mode')
		logger.info(f"Webhook GET params: mode={mode}, verify_token={verify_token}, challenge={challenge}, expected_token={self.VERIFY_TOKEN}")
		# For browser/manual GET, show the current VERIFY_TOKEN for debugging
		if not verify_token and not challenge and not mode:
			# Only return debug response if ALL are missing
			return Response({"verify_token": self.VERIFY_TOKEN, "all_params": dict(request.GET)}, status=status.HTTP_200_OK)
		from django.http import HttpResponse
		if mode == 'subscribe' and verify_token == self.VERIFY_TOKEN:
			return HttpResponse(challenge, status=200)
		return Response({"error": "Verification token mismatch", "received": verify_token, "expected": self.VERIFY_TOKEN, "mode": mode, "challenge": challenge, "all_params": dict(request.GET)}, status=status.HTTP_403_FORBIDDEN)
	def normalize_phone(self, phone):
		"""
		Normalize phone number to E.164 format (always with '+').
		Assumes WhatsApp always sends numbers in international format (no +).
		"""
		if not phone:
			return ''
		phone = str(phone).strip().replace(' ', '').replace('-', '')
		if phone.startswith('+'):
			phone = phone[1:]
		phone = phone.lstrip('0')
		# Always add '+' for storage/search
		return f'+{phone}'

	def post(self, request, *args, **kwargs):
		data = request.data
		# Handle WhatsApp webhook events
		entry = data.get('entry', [])
		for ent in entry:
			changes = ent.get('changes', [])
			for change in changes:
				value = change.get('value', {})
				messages = value.get('messages', [])
				statuses = value.get('statuses', [])
				# Handle incoming messages
				for msg in messages:
					from_number = msg.get('from')
					normalized_number = self.normalize_phone(from_number)
					text = msg.get('text', {}).get('body', '')
					wa_id = msg.get('id')
					customer, _ = Customer.objects.get_or_create(phone_number=normalized_number)
					# Prevent duplicate messages by whatsapp_message_id
					if not Message.objects.filter(whatsapp_message_id=wa_id).exists():
						Message.objects.create(
							customer=customer,
							content=text,
							direction='received',
							status='delivered',
							whatsapp_message_id=wa_id
						)
				# Handle delivery/read statuses
				for status in statuses:
					wa_id = status.get('id')
					status_str = status.get('status')
					Message.objects.filter(whatsapp_message_id=wa_id).update(status=status_str)
		return Response({"status": "received"}, status=status.HTTP_200_OK)
