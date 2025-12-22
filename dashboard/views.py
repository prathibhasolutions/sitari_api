from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect


from whatsapp.models import Customer, Message
from whatsapp.whatsapp_api import send_whatsapp_message


def privacy_view(request):
    return render(request, 'dashboard/privacy.html')


def terms_view(request):
    return render(request, 'dashboard/terms.html')


def get_customers_with_preview():
    """Get all customers with last message preview and unread count"""
    from django.db.models import Count, Q, Max
    customers = Customer.objects.annotate(
        unread_count=Count('messages', filter=Q(messages__direction='received', messages__is_read=False)),
        last_message_time=Max('messages__timestamp')
    ).order_by('-last_message_time', '-updated_at')
    
    # Add last message to each customer
    customer_list = []
    for c in customers:
        last_msg = Message.objects.filter(customer=c).order_by('-timestamp').first()
        c.last_message = last_msg.content[:30] + '...' if last_msg and len(last_msg.content) > 30 else (last_msg.content if last_msg else '')
        c.last_message_time_display = last_msg.timestamp.strftime('%H:%M') if last_msg else ''
        if last_msg and last_msg.media and not last_msg.content:
            c.last_message = '📷 Photo' if 'image' in (last_msg.media_type or '') else '📎 File'
        customer_list.append(c)
    return customer_list


def dashboard_home(request):
    total_customers = Customer.objects.count()
    total_messages = Message.objects.count()
    sent_messages = Message.objects.filter(direction='sent').count()
    received_messages = Message.objects.filter(direction='received').count()
    customers = get_customers_with_preview()
    context = {
        'total_customers': total_customers,
        'total_messages': total_messages,
        'sent_messages': sent_messages,
        'received_messages': received_messages,
        'customers': customers,
    }
    return render(request, 'dashboard/home.html', context)

def chat_view(request, customer_id):
    import logging
    import mimetypes
    logger = logging.getLogger("dashboard.chat")
    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == 'POST':
        content = request.POST.get('content', '')
        media = request.FILES.get('media')
        wa_id = None
        from whatsapp.whatsapp_api import send_whatsapp_media
        logger.info(f"Sending message to {customer.phone_number}: {content}")
        # If media is uploaded, send it to WhatsApp
        if media:
            # Determine media type from file
            mime_type = media.content_type or mimetypes.guess_type(media.name)[0] or 'application/octet-stream'
            logger.info(f"Uploading media: {media.name}, type: {mime_type}")
            
            # Determine WhatsApp media type
            if mime_type.startswith('image/'):
                wa_media_type = 'image'
            else:
                wa_media_type = 'document'
            
            # Save the file first to get its URL
            msg = Message.objects.create(
                customer=customer,
                content=content,
                media=media,
                media_type=mime_type,
                direction='sent',
                status='pending',
            )
            # Build public URL for media (update to your actual domain)
            public_url = request.build_absolute_uri(msg.media.url)
            logger.info(f"Sending {wa_media_type} via WhatsApp: {public_url}")
            api_response = send_whatsapp_media(
                customer.phone_number,
                public_url,
                media_type=wa_media_type,
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
            if content and content.strip():
                api_response = send_whatsapp_message(customer.phone_number, template_name=None, text=content)
                print(f"[DEBUG] API Response: {api_response}")
            else:
                print(f"[DEBUG] Content is empty, not sending!")
                api_response = {}
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
    # Mark received messages as read
    Message.objects.filter(customer=customer, direction='received', is_read=False).update(is_read=True)
    # Pass all customers for sidebar navigation with preview
    customers = get_customers_with_preview()
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
        # Use saved media_type if available, otherwise guess from extension
        if m.media_type:
            media_type = m.media_type
        elif m.media:
            import mimetypes
            guessed_type, _ = mimetypes.guess_type(media_url)
            media_type = guessed_type or ''
        else:
            media_type = ''
        data.append({
            'content': m.content,
            'direction': m.direction,
            'timestamp': m.timestamp.strftime('%b %d, %Y %H:%M'),
            'status': m.status.title(),
            'media_url': media_url,
            'media_type': media_type,
        })
    return JsonResponse({'messages': data})
