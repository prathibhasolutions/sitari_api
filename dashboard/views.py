from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from whatsapp.models import Customer, Message
from whatsapp.whatsapp_api import send_whatsapp_message

@login_required
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

@login_required
def chat_view(request, customer_id):
    customer = get_object_or_404(Customer, id=customer_id)
    messages = Message.objects.filter(customer=customer).order_by('timestamp')
    api_response = None
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Send WhatsApp message
            api_response = send_whatsapp_message(customer.phone_number, template_name=None, text=content)
            Message.objects.create(
                customer=customer,
                content=content,
                direction='sent',
                status='pending',
            )
    return render(request, 'dashboard/chat.html', {
        'customer': customer,
        'messages': messages,
        'api_response': api_response,
    })
