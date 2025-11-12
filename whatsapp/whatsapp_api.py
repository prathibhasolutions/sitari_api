import os
import requests

WHATSAPP_ACCESS_TOKEN = "EAAac186RskkBP0XuzaZAZASONTm0vVOogPAZAqMi3uZB5muwZAjrT3JwQgcQHa51UBapg5VaTBGaPPEWfovA7CXum8CorrEVm9zzN3N2goNFEMZBZBDWJD20qQfQ11sY0KxQy3gcIkRTLMqepHWBmkqDuEZBamnWOENJAJxYeP5g4R9MEAFLMHypuZASLiUvZA7b8iy0zSUd7IxJj86Ikg1ZCABLbV6haNXZCaSCyRc6DOm93cJn2uvIqm5oM6kZC2z0SZCgtNlnMAGeTprZAh46pFB38Yj"
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
