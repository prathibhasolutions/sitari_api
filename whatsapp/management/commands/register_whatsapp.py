from django.core.management.base import BaseCommand
from whatsapp.whatsapp_api import register_phone_number


class Command(BaseCommand):
    help = 'Register the WhatsApp phone number with the Cloud API'

    def add_arguments(self, parser):
        parser.add_argument('--pin', type=str, default='123456', help='6-digit PIN for registration')

    def handle(self, *args, **options):
        pin = options['pin']
        self.stdout.write(f"Registering phone number with PIN: {pin}")
        result = register_phone_number(pin=pin)
        self.stdout.write(self.style.SUCCESS(f"Result: {result}"))
