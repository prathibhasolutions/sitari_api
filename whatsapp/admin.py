from django.contrib import admin
from .models import Customer, Message, Template

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
	list_display = ("name", "phone_number", "email", "created_at")
	search_fields = ("name", "phone_number", "email")


from django.utils.html import format_html
from .whatsapp_api import send_whatsapp_message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
	list_display = ("customer", "direction", "status", "timestamp", "send_now")
	list_filter = ("direction", "status")
	search_fields = ("customer__name", "customer__phone_number", "content")

	def send_now(self, obj):
		if obj.direction == 'sent':
			return "Already sent"
		return format_html(
			'<a class="button" href="/admin/whatsapp/message/{}/send/">Send</a>', obj.id
		)
	send_now.short_description = 'Send WhatsApp'

	def get_urls(self):
		from django.urls import path
		urls = super().get_urls()
		custom_urls = [
			path('<int:message_id>/send/', self.admin_site.admin_view(self.send_message_view), name='send-whatsapp-message'),
		]
		return custom_urls + urls

	def send_message_view(self, request, message_id):
		from django.shortcuts import redirect, get_object_or_404
		obj = get_object_or_404(Message, pk=message_id)
		if obj.direction == 'sent':
			self.message_user(request, "Message already sent.")
		else:
			resp = send_whatsapp_message(obj.customer.phone_number)
			obj.direction = 'sent'
			obj.status = 'pending'
			obj.save()
			self.message_user(request, f"WhatsApp message sent. API response: {resp}")
		return redirect(f'/admin/whatsapp/message/{message_id}/change/')

@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
	list_display = ("name", "language", "created_at")
	search_fields = ("name",)
	actions = ["send_template_to_all_customers"]

	def send_template_to_all_customers(self, request, queryset):
		customers = Customer.objects.all()
		for template in queryset:
			for customer in customers:
				send_whatsapp_message(customer.phone_number, template.name)
		self.message_user(request, "Template(s) sent to all customers.")
	send_template_to_all_customers.short_description = "Send selected template(s) to all customers"
