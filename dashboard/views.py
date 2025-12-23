from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages as django_messages

from whatsapp.models import Customer, Message, Agent
from whatsapp.whatsapp_api import send_whatsapp_message


def portal_view(request):
    """Main portal page with login options for agents and admin"""
    return render(request, 'dashboard/portal.html')


def agent_login_view(request):
    """Handle agent login with mobile number and password"""
    if request.method == 'POST':
        mobile = request.POST.get('mobile', '').strip()
        password = request.POST.get('password', '')
        
        try:
            agent = Agent.objects.get(mobile_number=mobile, is_active=True)
            if agent.check_password(password):
                # Store agent info in session
                request.session['agent_id'] = agent.id
                request.session['agent_name'] = agent.name
                request.session['is_agent'] = True
                return redirect('dashboard-home')
            else:
                return render(request, 'dashboard/portal.html', {
                    'agent_error': 'Invalid password. Please try again.'
                })
        except Agent.DoesNotExist:
            return render(request, 'dashboard/portal.html', {
                'agent_error': 'Agent not found or inactive. Please check your mobile number.'
            })
    
    return redirect('portal')


def admin_login_view(request):
    """Handle admin login with username and password"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_superuser:
                login(request, user)
                return redirect('dashboard-home')
            else:
                return render(request, 'dashboard/portal.html', {
                    'admin_error': 'Access denied. Only superusers can login here.'
                })
        else:
            return render(request, 'dashboard/portal.html', {
                'admin_error': 'Invalid username or password.'
            })
    
    return redirect('portal')


def logout_view(request):
    """Logout and clear session"""
    from django.contrib.auth import logout
    logout(request)
    request.session.flush()
    return redirect('portal')


def privacy_view(request):
    return render(request, 'dashboard/privacy.html')


def terms_view(request):
    return render(request, 'dashboard/terms.html')


def get_customers_with_preview(request):
    """Get customers with last message preview and unread count, filtered by user type"""
    from django.db.models import Count, Q, Max
    
    # Base queryset with annotations
    customers = Customer.objects.annotate(
        unread_count=Count('messages', filter=Q(messages__direction='received', messages__is_read=False)),
        last_message_time=Max('messages__timestamp')
    )
    
    # Filter based on user type - check agent session FIRST
    if request.session.get('is_agent'):
        # Agent sees only assigned customers
        agent_id = request.session.get('agent_id')
        customers = customers.filter(assigned_agent_id=agent_id).order_by('-last_message_time', '-updated_at')
    elif request.user.is_authenticated and request.user.is_superuser:
        # Admin sees all customers
        customers = customers.order_by('-last_message_time', '-updated_at')
    else:
        # No access
        customers = customers.none()
    
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


def check_access(request):
    """Check if user has access to dashboard"""
    return request.user.is_authenticated or request.session.get('is_agent')


def can_access_customer(request, customer):
    """Check if user can access a specific customer"""
    if request.session.get('is_agent'):
        # Agent can only access assigned customers
        agent_id = request.session.get('agent_id')
        return customer.assigned_agent_id == agent_id
    if request.user.is_authenticated and request.user.is_superuser:
        return True
    return False


def is_admin_user(request):
    """Check if user is admin (superuser and NOT logged in as agent)"""
    if request.session.get('is_agent'):
        return False
    return request.user.is_authenticated and request.user.is_superuser


def dashboard_home(request):
    if not check_access(request):
        return redirect('portal')
    
    # Get filtered customers based on user type
    customers = get_customers_with_preview(request)
    
    # Check if user is admin
    is_admin = is_admin_user(request)
    
    # Stats based on user access
    if is_admin:
        total_customers = Customer.objects.count()
        total_messages = Message.objects.count()
        sent_messages = Message.objects.filter(direction='sent').count()
        received_messages = Message.objects.filter(direction='received').count()
    else:
        agent_id = request.session.get('agent_id')
        customer_ids = Customer.objects.filter(assigned_agent_id=agent_id).values_list('id', flat=True)
        total_customers = len(customer_ids)
        total_messages = Message.objects.filter(customer_id__in=customer_ids).count()
        sent_messages = Message.objects.filter(customer_id__in=customer_ids, direction='sent').count()
        received_messages = Message.objects.filter(customer_id__in=customer_ids, direction='received').count()
    
    # Get all agents for assignment dropdown (admin only)
    agents = Agent.objects.filter(is_active=True) if is_admin else []
    
    # Get agent name if logged in as agent
    agent_name = request.session.get('agent_name', '')
    
    context = {
        'total_customers': total_customers,
        'total_messages': total_messages,
        'sent_messages': sent_messages,
        'received_messages': received_messages,
        'customers': customers,
        'agents': agents,
        'agent_name': agent_name,
        'is_agent': request.session.get('is_agent', False),
        'is_admin': is_admin,
    }
    return render(request, 'dashboard/home.html', context)

def chat_view(request, customer_id):
    if not check_access(request):
        return redirect('portal')
    
    import logging
    import mimetypes
    logger = logging.getLogger("dashboard.chat")
    customer = get_object_or_404(Customer, id=customer_id)
    
    # Check if user can access this customer
    if not can_access_customer(request, customer):
        return redirect('dashboard-home')
    
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
    customers = get_customers_with_preview(request)
    # Check if user is admin
    is_admin = is_admin_user(request)
    # Get all agents for assignment dropdown (admin only)
    agents = Agent.objects.filter(is_active=True) if is_admin else []
    # Get agent name if logged in as agent
    agent_name = request.session.get('agent_name', '')
    return render(request, 'dashboard/chat.html', {
        'customer': customer,
        'messages': messages,
        'customers': customers,
        'agents': agents,
        'agent_name': agent_name,
        'is_agent': request.session.get('is_agent', False),
        'is_admin': is_admin,
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


def assign_chat(request, customer_id):
    """Assign a customer chat to an agent (admin only)"""
    if not is_admin_user(request):
        return JsonResponse({'success': False, 'error': 'Unauthorized - admin access required'}, status=403)
    
    if request.method == 'POST':
        try:
            customer = get_object_or_404(Customer, id=customer_id)
            agent_id = request.POST.get('agent_id', '').strip()
            
            if agent_id:
                agent = Agent.objects.get(id=int(agent_id), is_active=True)
                customer.assigned_agent = agent
                customer.save()
                return JsonResponse({
                    'success': True,
                    'message': f'Chat assigned to {agent.name}',
                    'agent_name': agent.name
                })
            else:
                # Unassign
                customer.assigned_agent = None
                customer.save()
                return JsonResponse({
                    'success': True,
                    'message': 'Chat unassigned',
                    'agent_name': None
                })
        except Agent.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Agent not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)
