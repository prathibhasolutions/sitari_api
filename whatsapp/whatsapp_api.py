

import requests
from .models import WhatsAppConfig
WHATSAPP_PHONE_NUMBER_ID = "897101753497673"


def get_access_token():
    config = WhatsAppConfig.objects.order_by('-updated_at').first()
    return config.access_token if config else ''


def validate_message_content(text):
    """
    Validate message content for policy compliance (Policy Compliance - Content Validation)
    Returns: (is_valid, error_message)
    """
    if not text or not text.strip():
        return True, ""  # Empty is okay (might be media only)
    
    text_lower = text.lower()
    
    # Prohibited content keywords (customize as needed)
    prohibited_keywords = [
        # Adult content
        'porn', 'xxx', 'sex', 'adult content',
        # Drugs
        'cocaine', 'heroin', 'meth', 'drugs for sale',
        # Weapons
        'gun for sale', 'weapons for sale', 'buy gun',
        # Scams/Fraud
        'lottery winner', 'claim prize', 'send money now',
        # Hate speech
        'hate speech keywords here',
    ]
    
    for keyword in prohibited_keywords:
        if keyword in text_lower:
            return False, f"Message contains prohibited content: '{keyword}'"
    
    # Check message length (WhatsApp has 4096 char limit)
    if len(text) > 4096:
        return False, "Message too long (max 4096 characters)"
    
    # Check for excessive URLs (spam indicator)
    import re
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    if len(urls) > 3:
        return False, "Too many URLs in message (max 3)"
    
    # Check for repetitive content (spam indicator)
    words = text.split()
    if len(words) > 10:
        unique_words = set(words)
        if len(unique_words) / len(words) < 0.3:  # Less than 30% unique words
            return False, "Message appears to be spam (too repetitive)"
    
    return True, ""


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
