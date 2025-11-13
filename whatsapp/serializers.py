from rest_framework import serializers
from .models import Customer, Message, Template

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer(read_only=True)
    template = TemplateSerializer(read_only=True)
    customer_id = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all(), source='customer', write_only=True)
    template_id = serializers.PrimaryKeyRelatedField(queryset=Template.objects.all(), source='template', write_only=True, required=False, allow_null=True)
    media = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = Message
        fields = ['id', 'customer', 'customer_id', 'template', 'template_id', 'content', 'media', 'direction', 'status', 'timestamp', 'whatsapp_message_id']
