
from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class Agent(models.Model):
    """Agent model for agent portal login"""
    name = models.CharField(max_length=255)
    mobile_number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Mobile number for agent login"
    )
    password = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.mobile_number})"

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def save(self, *args, **kwargs):
        # Hash password if it's not already hashed
        if not self.password.startswith('pbkdf2_'):
            self.set_password(self.password)
        super().save(*args, **kwargs)


class WhatsAppConfig(models.Model):
	access_token = models.CharField(max_length=512, help_text="WhatsApp API Access Token")
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"WhatsAppConfig (updated {self.updated_at})"


class Customer(models.Model):
	OPT_IN_METHODS = [
		('whatsapp', 'WhatsApp Message'),
		('website', 'Website Form'),
		('sms', 'SMS'),
		('manual', 'Manual Entry'),
		('api', 'API'),
	]
	
	name = models.CharField(max_length=255, blank=True, default='')
	phone_number = models.CharField(
		max_length=20,
		unique=True,
		help_text="Enter the full phone number in international format, e.g., +919876543210"
	)
	email = models.EmailField(blank=True, null=True)
	assigned_agent = models.ForeignKey(
		'Agent',
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='assigned_customers',
		help_text="Agent assigned to handle this customer's chats"
	)
	
	# Opt-in/Opt-out tracking (Policy Compliance)
	opted_in = models.BooleanField(
		default=False,
		help_text="Customer has given consent to receive messages"
	)
	opt_in_method = models.CharField(
		max_length=20,
		choices=OPT_IN_METHODS,
		blank=True,
		null=True,
		help_text="How the customer opted in"
	)
	opt_in_date = models.DateTimeField(
		blank=True,
		null=True,
		help_text="When customer opted in"
	)
	opted_out = models.BooleanField(
		default=False,
		help_text="Customer has unsubscribed"
	)
	opt_out_date = models.DateTimeField(
		blank=True,
		null=True,
		help_text="When customer opted out"
	)
	
	# 12-hour conversation window tracking (safer than 24hr policy)
	last_message_from_customer = models.DateTimeField(
		blank=True,
		null=True,
		help_text="Last time customer sent a message (for 12hr window)"
	)
	
	# Blocking/Safety
	is_blocked = models.BooleanField(
		default=False,
		help_text="Block this customer from receiving messages"
	)
	
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def clean_phone_number(self, phone):
		"""Clean phone number to WhatsApp format (no +, spaces, or dashes)"""
		if phone:
			# Remove +, spaces, dashes, and parentheses
			return phone.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
		return phone

	def save(self, *args, **kwargs):
		"""Override save to clean phone number"""
		self.phone_number = self.clean_phone_number(self.phone_number)
		super().save(*args, **kwargs)

	def __str__(self):
		return f"{self.name} ({self.phone_number})" if self.name else self.phone_number
	
	def display_name(self):
		"""Return name if available, otherwise phone number"""
		return self.name if self.name else self.phone_number
	
	def can_send_message(self):
		"""Check if we can send messages to this customer (Policy Compliance)"""
		from django.utils import timezone
		from datetime import timedelta
		
		# Blocked customers cannot receive messages
		if self.is_blocked:
			return False, "Customer is blocked"
		
		# Customer must have opted in
		if not self.opted_in:
			return False, "Customer has not opted in to receive messages"
		
		# Customer must not have opted out
		if self.opted_out:
			return False, "Customer has opted out"
		
		return True, "OK"
	
	def is_within_24hr_window(self):
		"""Check if we're within 12-hour conversation window (safer than 24hr)"""
		from django.utils import timezone
		from datetime import timedelta
		
		if not self.last_message_from_customer:
			return False
		
		time_since_last_message = timezone.now() - self.last_message_from_customer
		return time_since_last_message < timedelta(hours=12)
	
	def can_send_freeform_text(self):
		"""Check if we can send free-form text (not template)"""
		can_send, reason = self.can_send_message()
		if not can_send:
			return False, reason
		
		if not self.is_within_24hr_window():
			return False, "Outside 12-hour conversation window. Use message template instead."
		
		return True, "OK"
	
	def check_rate_limit(self):
		"""Check if we're sending too many messages (Policy Compliance - Spam Prevention)"""
		from django.utils import timezone
		from datetime import timedelta
		
		# Count messages sent in last hour
		one_hour_ago = timezone.now() - timedelta(hours=1)
		messages_last_hour = Message.objects.filter(
			customer=self,
			direction='sent',
			timestamp__gte=one_hour_ago
		).count()
		
		# Limit: 50 messages per hour per customer (adjust as needed)
		if messages_last_hour >= 50:
			return False, f"Rate limit exceeded. {messages_last_hour} messages sent in last hour. Please wait before sending more."
		
		# Count messages sent today
		today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
		messages_today = Message.objects.filter(
			customer=self,
			direction='sent',
			timestamp__gte=today_start
		).count()
		
		# Limit: 200 messages per day per customer (adjust as needed)
		if messages_today >= 200:
			return False, f"Daily limit exceeded. {messages_today} messages sent today. Try again tomorrow."
		
		return True, "OK"
	
	def opt_out(self):
		"""Mark customer as opted out (Policy Compliance)"""
		from django.utils import timezone
		self.opted_out = True
		self.opt_out_date = timezone.now()
		self.save()
	
	def opt_in_customer(self, method='manual'):
		"""Manually opt-in a customer"""
		from django.utils import timezone
		self.opted_in = True
		self.opted_out = False
		self.opt_in_method = method
		self.opt_in_date = timezone.now()
		self.opt_out_date = None
		self.save()


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
	content = models.TextField(blank=True)
	media = models.FileField(upload_to='chat_media/', blank=True, null=True)
	media_type = models.CharField(max_length=100, blank=True, null=True, help_text="MIME type of the media file")
	direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
	status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
	timestamp = models.DateTimeField(auto_now_add=True)
	whatsapp_message_id = models.CharField(max_length=100, blank=True, null=True)
	is_read = models.BooleanField(default=False, help_text="Whether message has been read in dashboard")
	
	# Quality tracking (Policy Compliance)
	delivered_at = models.DateTimeField(blank=True, null=True, help_text="When message was delivered")
	read_at = models.DateTimeField(blank=True, null=True, help_text="When message was read by recipient")
	failed_at = models.DateTimeField(blank=True, null=True, help_text="When message failed")
	error_code = models.CharField(max_length=50, blank=True, null=True, help_text="WhatsApp API error code")
	error_message = models.TextField(blank=True, null=True, help_text="WhatsApp API error message")

	def __str__(self):
		return f"{self.direction.title()} to {self.customer.phone_number} at {self.timestamp}" 
