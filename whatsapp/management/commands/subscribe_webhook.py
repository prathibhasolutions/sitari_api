from django.core.management.base import BaseCommand
from whatsapp.whatsapp_api import get_access_token
import requests


class Command(BaseCommand):
    help = 'Subscribe webhook to a WhatsApp Business Account'

    def add_arguments(self, parser):
        parser.add_argument('--waba-id', type=str, required=True, help='WhatsApp Business Account ID')

    def handle(self, *args, **options):
        access_token = get_access_token()
        waba_id = options['waba_id']
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Subscribe the app to the WABA
        url = f"https://graph.facebook.com/v19.0/{waba_id}/subscribed_apps"
        
        response = requests.post(url, headers=headers)
        result = response.json()
        
        if 'success' in result and result['success']:
            self.stdout.write(self.style.SUCCESS(f"Successfully subscribed webhook to WABA {waba_id}"))
        else:
            self.stdout.write(self.style.ERROR(f"Failed: {result}"))
        
        # Check current subscriptions
        self.stdout.write("\nChecking current subscriptions...")
        response = requests.get(url, headers=headers)
        self.stdout.write(f"Subscribed apps: {response.json()}")
