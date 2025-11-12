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
					text = msg.get('text', {}).get('body', '')
					wa_id = msg.get('id')
					customer, _ = Customer.objects.get_or_create(phone_number=from_number)
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
