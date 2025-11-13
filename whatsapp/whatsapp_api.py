

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


#
# Add correct send_whatsapp_media function at the end
def send_whatsapp_media(to_number, media_url, media_type='image', caption=None):
    """
    Send a media message (image/document) to WhatsApp using a public media URL.
    media_type: 'image' or 'document'
    """
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    if media_type == 'image':
        media_payload = {
            "link": media_url
        }
        if caption:
            media_payload["caption"] = caption
        data = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "image",
            "image": media_payload
        }
    elif media_type == 'document':
        data = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "document",
            "document": {
                "link": media_url
            }
        }
    else:
        raise ValueError("media_type must be 'image' or 'document'")
    response = requests.post(url, headers=headers, json=data)
    return response.json()