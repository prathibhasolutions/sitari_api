from django.core.management.base import BaseCommand
from whatsapp.whatsapp_api import get_access_token
import requests


class Command(BaseCommand):
    help = 'Get WhatsApp Business Account info and Phone Number IDs'

    def add_arguments(self, parser):
        parser.add_argument('--waba-id', type=str, help='WhatsApp Business Account ID')
        parser.add_argument('--business-id', type=str, help='Business ID')

    def handle(self, *args, **options):
        access_token = get_access_token()
        
        if not access_token:
            self.stdout.write(self.style.ERROR("No access token found in database!"))
            return
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        waba_id = options.get('waba_id')
        business_id = options.get('business_id')
        
        if business_id:
            # Get WABAs from business
            waba_url = f"https://graph.facebook.com/v19.0/{business_id}/owned_whatsapp_business_accounts"
            response = requests.get(waba_url, headers=headers)
            waba_result = response.json()
            self.stdout.write(f"WABAs: {waba_result}")
            
            if 'data' in waba_result:
                for waba in waba_result['data']:
                    waba_id = waba.get('id')
                    self.stdout.write(self.style.SUCCESS(f"\n=== WABA ID: {waba_id} ==="))
        
        if waba_id:
            # Get phone numbers from WABA
            phones_url = f"https://graph.facebook.com/v19.0/{waba_id}/phone_numbers"
            response = requests.get(phones_url, headers=headers)
            phones = response.json()
            self.stdout.write(f"\nPhone Numbers Response: {phones}")
            
            if 'data' in phones:
                for phone in phones['data']:
                    self.stdout.write(self.style.SUCCESS(
                        f"\n{'='*50}\n"
                        f">>> Phone: {phone.get('display_phone_number')}\n"
                        f">>> PHONE NUMBER ID: {phone.get('id')}\n"
                        f">>> Verified Name: {phone.get('verified_name')}\n"
                        f">>> Status: {phone.get('code_verification_status')}\n"
                        f"{'='*50}"
                    ))
        
        if not waba_id and not business_id:
            self.stdout.write(self.style.WARNING(
                "\nUsage:\n"
                "  python manage.py get_whatsapp_info --waba-id YOUR_WABA_ID\n"
                "  python manage.py get_whatsapp_info --business-id YOUR_BUSINESS_ID\n"
                "\nTo find your WABA ID:\n"
                "  1. Go to Meta Business Suite -> Business Settings\n"
                "  2. Click 'Accounts' -> 'WhatsApp Accounts'\n"
                "  3. Click on your account - the WABA ID is in the URL\n"
                "\nOr check the URL when viewing your WhatsApp account:\n"
                "  business.facebook.com/settings/whatsapp-accounts/WABA_ID_HERE"
            ))
