from django.db import models


class Customer(models.Model):
	name = models.CharField(max_length=255)
	phone_number = models.CharField(
		max_length=20,
		unique=True,
		help_text="Enter the full phone number in international format, e.g., +919876543210"
	)
	email = models.EmailField(blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.name} ({self.phone_number})"


class Template(models.Model):
	name = models.CharField(max_length=100, unique=True)
	body = models.TextField()
	language = models.CharField(max_length=10, default='en')
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.name


class Message(models.Model):
	DIRECTION_CHOICES = (
		('sent', 'Sent'),
		('received', 'Received'),
	)
	STATUS_CHOICES = (
		('pending', 'Pending'),
		('sent', 'Sent'),
		('delivered', 'Delivered'),
		('read', 'Read'),
		('failed', 'Failed'),
	)
	customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='messages')
	template = models.ForeignKey(Template, on_delete=models.SET_NULL, null=True, blank=True)
	content = models.TextField()
	direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
	status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
	timestamp = models.DateTimeField(auto_now_add=True)
	whatsapp_message_id = models.CharField(max_length=100, blank=True, null=True)

	def __str__(self):
		return f"{self.direction.title()} to {self.customer.phone_number} at {self.timestamp}" 
