from django.http import JsonResponse
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
    if request.method == 'POST':
        content = request.POST.get('content', '')
        media = request.FILES.get('media')
        wa_id = None
        from whatsapp.whatsapp_api import send_whatsapp_media
        # If media is uploaded, send it to WhatsApp
        if media:
            # Save the file first to get its URL
            msg = Message.objects.create(
                customer=customer,
                content=content,
                media=media,
                direction='sent',
                status='pending',
            )
            # Build public URL for media (update to your actual domain)
            public_url = request.build_absolute_uri(msg.media.url)
            api_response = send_whatsapp_media(
                customer.phone_number,
                public_url,
                media_type='image',
                caption=content if content else None
            )
            if isinstance(api_response, dict):
                api_messages = api_response.get('messages')
                if api_messages and isinstance(api_messages, list) and 'id' in api_messages[0]:
                    wa_id = api_messages[0]['id']
                elif 'messages' in api_response and isinstance(api_response['messages'], list):
                    wa_id = api_response['messages'][0].get('id')
                elif 'id' in api_response:
                    wa_id = api_response['id']
            msg.whatsapp_message_id = wa_id
            msg.save()
        else:
            # Send WhatsApp message (text only)
            api_response = send_whatsapp_message(customer.phone_number, template_name=None, text=content)
            if isinstance(api_response, dict):
                api_messages = api_response.get('messages')
                if api_messages and isinstance(api_messages, list) and 'id' in api_messages[0]:
                    wa_id = api_messages[0]['id']
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
        # Redirect to chat page to prevent duplicate sending on reload
        from django.urls import reverse
        return redirect(reverse('dashboard-chat', args=[customer.id]))
    messages = Message.objects.filter(customer=customer).order_by('timestamp')
    # Pass all customers for sidebar navigation
    customers = Customer.objects.all().order_by('-updated_at')
    return render(request, 'dashboard/chat.html', {
        'customer': customer,
        'messages': messages,
        'customers': customers,
    })

def chat_messages_api(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    messages = Message.objects.filter(customer=customer).order_by('timestamp')
    data = []
    for m in messages:
        media_url = m.media.url if m.media else ''
        media_type = ''
        if m.media and hasattr(m.media, 'file') and hasattr(m.media.file, 'content_type'):
            media_type = m.media.file.content_type
        data.append({
            'content': m.content,
            'direction': m.direction,
            'timestamp': m.timestamp.strftime('%b %d, %Y %H:%M'),
            'status': m.status.title(),
            'media_url': media_url,
            'media_type': media_type,
        })
    return JsonResponse({'messages': data})
    return render(request, 'dashboard/chat.html', {
        'customer': customer,
        'messages': messages,
    })
