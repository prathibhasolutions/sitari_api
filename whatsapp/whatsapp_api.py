

import requests
from .models import WhatsAppConfig
WHATSAPP_PHONE_NUMBER_ID = "929579463571953"


def get_access_token():
    config = WhatsAppConfig.objects.order_by('-updated_at').first()
    return config.access_token if config else ''


def register_phone_number(pin="123456"):
    """
    Register the phone number with WhatsApp Cloud API.
    This completes the phone registration process after adding the certificate.
    """
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/register"
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "pin": pin
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()


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
def send_whatsapp_media(to_number, media_url, media_type='image', caption=None, filename=None):
    """
    Send a media message (image/document/video) to WhatsApp using a public media URL.
    media_type: 'image', 'document', 'video', 'audio'
    """
    import logging
    logger = logging.getLogger("whatsapp.api")
    
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    if media_type == 'image':
        media_payload = {"link": media_url}
        if caption:
            media_payload["caption"] = caption
        data = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "image",
            "image": media_payload
        }
    elif media_type == 'document':
        media_payload = {"link": media_url}
        if caption:
            media_payload["caption"] = caption
        if filename:
            media_payload["filename"] = filename
        data = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "document",
            "document": media_payload
        }
    elif media_type == 'video':
        media_payload = {"link": media_url}
        if caption:
            media_payload["caption"] = caption
        data = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "video",
            "video": media_payload
        }
    elif media_type == 'audio':
        data = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "audio",
            "audio": {"link": media_url}
        }
    else:
        # Default to document for unknown types
        media_payload = {"link": media_url}
        if filename:
            media_payload["filename"] = filename
        data = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "document",
            "document": media_payload
        }
    
    logger.info(f"Sending {media_type} to {to_number}: {media_url}")
    response = requests.post(url, headers=headers, json=data)
    result = response.json()
    logger.info(f"WhatsApp API response: {result}")
    return result
