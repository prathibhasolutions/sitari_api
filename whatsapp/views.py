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
		import logging
		logger = logging.getLogger("whatsapp.webhook")
		data = request.data
		logger.info(f"Webhook POST received: {data}")
		# Handle WhatsApp webhook events
		entry = data.get('entry', [])
		for ent in entry:
			changes = ent.get('changes', [])
			for change in changes:
				value = change.get('value', {})
				messages = value.get('messages', [])
				statuses = value.get('statuses', [])
				contacts = value.get('contacts', [])
				
				# Build a map of wa_id -> profile name from contacts
				contact_names = {}
				for contact in contacts:
					wa_id = contact.get('wa_id')
					profile = contact.get('profile', {})
					name = profile.get('name', '')
					if wa_id and name:
						contact_names[wa_id] = name
				
				logger.info(f"Processing {len(messages)} messages, {len(statuses)} statuses, contacts: {contact_names}")
				
				# Handle incoming messages
				for msg in messages:
					from_number = msg.get('from')
					normalized_number = self.normalize_phone(from_number)
					wa_id = msg.get('id')
					
					# Get profile name from contacts
					profile_name = contact_names.get(from_number, '')
					logger.info(f"Message from {from_number} -> normalized: {normalized_number}, wa_id: {wa_id}, profile: {profile_name}")
					
					customer, created = Customer.objects.get_or_create(phone_number=normalized_number)
					
					# Update customer name if we got a profile name and customer has no name or just phone number
					if profile_name and (not customer.name or customer.name == normalized_number or customer.name.startswith('+')):
						customer.name = profile_name
						customer.save()
						logger.info(f"Updated customer name to: {profile_name}")
					
					logger.info(f"Customer {'created' if created else 'found'}: {customer.id}")
					# Handle text and media
					text = msg.get('text', {}).get('body', '')
					media_url = None
					media_type = None
					# Check for image
					if msg.get('type') == 'image' and 'image' in msg:
						media_id = msg['image'].get('id')
						logger.info(f"Processing image with media_id: {media_id}")
						# Download media from WhatsApp
						media_path, media_type = self.download_whatsapp_media(media_id)
						logger.info(f"Downloaded image: path={media_path}, type={media_type}")
					# Check for document
					elif msg.get('type') == 'document' and 'document' in msg:
						media_id = msg['document'].get('id')
						logger.info(f"Processing document with media_id: {media_id}")
						media_path, media_type = self.download_whatsapp_media(media_id)
						logger.info(f"Downloaded document: path={media_path}, type={media_type}")
					# Check for video
					elif msg.get('type') == 'video' and 'video' in msg:
						media_id = msg['video'].get('id')
						logger.info(f"Processing video with media_id: {media_id}")
						media_path, media_type = self.download_whatsapp_media(media_id)
						logger.info(f"Downloaded video: path={media_path}, type={media_type}")
					# Check for audio
					elif msg.get('type') == 'audio' and 'audio' in msg:
						media_id = msg['audio'].get('id')
						logger.info(f"Processing audio with media_id: {media_id}")
						media_path, media_type = self.download_whatsapp_media(media_id)
						logger.info(f"Downloaded audio: path={media_path}, type={media_type}")
					else:
						media_path = None
						media_type = None
					
					# Prevent duplicate messages by whatsapp_message_id
					if not Message.objects.filter(whatsapp_message_id=wa_id).exists():
						msg_obj = Message(
							customer=customer,
							content=text,
							direction='received',
							status='delivered',
							whatsapp_message_id=wa_id
						)
						# Save media path if present
						if media_path:
							msg_obj.media.name = media_path
							msg_obj.media_type = media_type
							logger.info(f"Saved media to message: {media_path}")
						msg_obj.save()
						logger.info(f"Message saved with id: {msg_obj.id}")

		# Handle delivery/read statuses
		for ent in entry:
			changes = ent.get('changes', [])
			for change in changes:
				value = change.get('value', {})
				statuses = value.get('statuses', [])
				for status_obj in statuses:
					wa_id = status_obj.get('id')
					status_str = status_obj.get('status')  # sent, delivered, read, failed
					logger.info(f"Status update: wa_id={wa_id}, status={status_str}")
					updated = Message.objects.filter(whatsapp_message_id=wa_id).update(status=status_str)
					logger.info(f"Updated {updated} messages with status {status_str}")
		return Response({"status": "received"}, status=status.HTTP_200_OK)

	def download_whatsapp_media(self, media_id):
		"""
		Download media from WhatsApp using media_id and return (local_path, content_type)
		"""
		import logging
		import requests
		import os
		from django.conf import settings
		from .whatsapp_api import get_access_token
		
		logger = logging.getLogger("whatsapp.webhook")
		access_token = get_access_token()
		
		# Step 1: Get media URL from WhatsApp
		url = f"https://graph.facebook.com/v19.0/{media_id}"
		headers = {"Authorization": f"Bearer {access_token}"}
		logger.info(f"Fetching media info for media_id: {media_id}")
		
		resp = requests.get(url, headers=headers)
		logger.info(f"Media info response: status={resp.status_code}")
		
		if resp.status_code != 200:
			logger.error(f"Failed to get media URL: {resp.text}")
			return None, None
			
		media_data = resp.json()
		media_url = media_data.get('url')
		mime_type = media_data.get('mime_type', 'application/octet-stream')
		logger.info(f"Media URL: {media_url}, mime_type: {mime_type}")
		
		if not media_url:
			logger.error("No media URL in response")
			return None, None
		
		# Step 2: Download the actual media file (requires auth header!)
		media_resp = requests.get(media_url, headers=headers)
		logger.info(f"Media download response: status={media_resp.status_code}, size={len(media_resp.content)}")
		
		if media_resp.status_code != 200:
			logger.error(f"Failed to download media: {media_resp.text}")
			return None, None
		
		# Step 3: Save to local file
		# Determine file extension from mime_type
		ext_map = {
			'image/jpeg': 'jpg',
			'image/png': 'png',
			'image/gif': 'gif',
			'image/webp': 'webp',
			'application/pdf': 'pdf',
			'video/mp4': 'mp4',
			'audio/ogg': 'ogg',
			'audio/mpeg': 'mp3',
			'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
			'application/msword': 'doc',
		}
		ext = ext_map.get(mime_type, mime_type.split('/')[-1] if '/' in mime_type else 'bin')
		
		# Create media directory if not exists
		media_dir = os.path.join(settings.MEDIA_ROOT, 'chat_media')
		os.makedirs(media_dir, exist_ok=True)
		
		# Save file
		filename = f"{media_id}.{ext}"
		file_path = os.path.join(media_dir, filename)
		
		with open(file_path, 'wb') as f:
			f.write(media_resp.content)
		
		logger.info(f"Media saved to: {file_path}")
		
		# Return relative path and mime type
		return f"chat_media/{filename}", mime_type

	# Move status handling to correct indentation
	# ...existing code...


class DebugConfigView(APIView):
	"""Debug endpoint to check WhatsApp configuration"""
	def get(self, request):
		from .whatsapp_api import WHATSAPP_PHONE_NUMBER_ID, get_access_token
		token = get_access_token()
		return Response({
			"phone_number_id": WHATSAPP_PHONE_NUMBER_ID,
			"token_exists": bool(token),
			"token_preview": token[:20] + "..." if token else None
		})
