
import requests
from .models import WhatsAppConfig
WHATSAPP_PHONE_NUMBER_ID = "830174150185579"


def get_access_token():
    config = WhatsAppConfig.objects.order_by('-updated_at').first()
    return config.access_token if config else ''

def send_whatsapp_message(to_number, template_name="hello_world", text=None):
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    if text:
        data = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {"body": text}
        }
    else:
        data = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": { "code": "en_US" }
            }
        }
    response = requests.post(url, headers=headers, json=data)
    return response.json()
