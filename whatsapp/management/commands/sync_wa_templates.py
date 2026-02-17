import requests
from django.core.management.base import BaseCommand
from whatsapp.models import Template, WhatsAppConfig

class Command(BaseCommand):
    help = 'Sync approved WhatsApp templates from Meta Business API'

    def handle(self, *args, **options):
        config = WhatsAppConfig.objects.first()
        if not config or not config.access_token:
            self.stderr.write(self.style.ERROR('WhatsAppConfig with access_token required.'))
            return

        access_token = config.access_token
        # Use WABA_ID from whatsapp_api.py for consistency
        from whatsapp.whatsapp_api import WHATSAPP_PHONE_NUMBER_ID
        # WABA_ID is usually the same as the phone number's business account id; update if needed
        WABA_ID = '897101753497673'  # Set to your actual WABA ID if different
        url = f'https://graph.facebook.com/v19.0/{WABA_ID}/message_templates?access_token={access_token}'
        response = requests.get(url)
        if response.status_code != 200:
            self.stderr.write(self.style.ERROR(f'API error: {response.status_code} {response.text}'))
            return
        data = response.json()
        templates = data.get('data', [])
        count = 0
        for t in templates:
            if t.get('status') == 'APPROVED':
                obj, created = Template.objects.update_or_create(
                    name=t['name'],
                    defaults={
                        'body': t['components'][0]['text'] if t.get('components') and t['components'][0].get('text') else '',
                        'language': t.get('language', 'en'),
                        'is_approved': True,
                        'wa_id': t.get('id', None),
                    }
                )
                count += 1
        # Mark all other templates as not approved
        Template.objects.exclude(name__in=[t['name'] for t in templates if t.get('status') == 'APPROVED']).update(is_approved=False)
        self.stdout.write(self.style.SUCCESS(f'Synced {count} approved templates.'))
