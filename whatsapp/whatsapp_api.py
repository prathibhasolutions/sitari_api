import os
import requests

WHATSAPP_ACCESS_TOKEN = "EAAac186RskkBP3iG0yDWKxYhtmIqynjWBNoADt4HQzmlOPqcGgxTgFZAaNoKo8xmxDGr1WFqNZAwzChgN7gIScGfyo7y4wIC0WX9KMvYF9ePKNZCqZCs0lBCToDHxoQYjg6gkoIWNiFqPmoyutloOClZAa4un5AEbg4hJHjwH89D0DqZBy6zAGDVJDUF1ib8D6nehSEyJK60Xf7v6GjskdMxIqiNtLnZCedzzhimmyMwmZAFmrZCjJUO87LNwwj6BfsLLqKlsvGGp0zJZCrVfqzfVr"
WHATSAPP_PHONE_NUMBER_ID = "830174150185579"


def send_whatsapp_message(to_number, template_name="hello_world", text=None):
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
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
