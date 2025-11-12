from django.shortcuts import render, get_object_or_404, redirect


from whatsapp.models import Customer, Message
from whatsapp.whatsapp_api import send_whatsapp_message

def dashboard_home(request):
    total_customers = Customer.objects.count()
    total_messages = Message.objects.count()
    sent_messages = Message.objects.filter(direction='sent').count()
    received_messages = Message.objects.filter(direction='received').count()
    customers = Customer.objects.all().order_by('-updated_at')
    context = {
        'total_customers': total_customers,
        'total_messages': total_messages,
        'sent_messages': sent_messages,
        'received_messages': received_messages,
        'customers': customers,
    }
    return render(request, 'dashboard/home.html', context)

def chat_view(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    messages = Message.objects.filter(customer=customer).order_by('timestamp')
    api_response = None
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Send WhatsApp message
            api_response = send_whatsapp_message(customer.phone_number, template_name=None, text=content)
            wa_id = None
            # Try to extract WhatsApp message id from API response
            if isinstance(api_response, dict):
                messages = api_response.get('messages')
                if messages and isinstance(messages, list) and 'id' in messages[0]:
                    wa_id = messages[0]['id']
                elif 'messages' in api_response and isinstance(api_response['messages'], list):
                    wa_id = api_response['messages'][0].get('id')
                elif 'id' in api_response:
                    wa_id = api_response['id']
            Message.objects.create(
                customer=customer,
                content=content,
                direction='sent',
                status='pending',
                whatsapp_message_id=wa_id
            )
    return render(request, 'dashboard/chat.html', {
        'customer': customer,
        'messages': messages,
        'api_response': api_response,
    })
