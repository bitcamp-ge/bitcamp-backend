from rest_framework import serializers
from . import models
from content.serializers import ProgramSerializer, ServiceSerializer


class BitCampUserSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = models.BitCampUser
        fields = [
            "id", "first_name", "last_name", "phone_number", "email", "username", "password"
        ]
        

class PaymentSerializer(serializers.ModelSerializer):
    title = serializers.ReadOnlyField()

    class Meta:
        model = models.Payment
        fields = [
            'id', 'enrollment', 'amount', 'status', 
            'payze_transactionId', 'payze_paymentId', 'cardMask', 'token', 
            'paymentUrl', 'title'
        ]


class EnrollmentSerializer(serializers.ModelSerializer):
    payments = PaymentSerializer(many=True, read_only=True)
    # Adjust the field names to match the model's field names
    program = ProgramSerializer(read_only=True, source='program_id')
    service = ServiceSerializer(read_only=True, source='service_id')

    class Meta:
        model = models.Enrollment
        fields = [
            "id", "enrollment_date", "enrollment_cancel_date", "user", 
            "service_id", "program_id", "mentor_id", "status", "start_payment", "last_payment", 
            "payments", "program", "service"
        ]

    def create(self, validated_data):
        user = self.context.get("user")
        if user:
            validated_data["user"] = user
        return super().create(validated_data)
    
    
class KidsProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.KidsProfile
        fields = "__all__"