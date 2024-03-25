from django.contrib.auth.models import AbstractUser
from django.db import models
from content import models as content
from django.utils.functional import cached_property
from django.contrib import admin


class BitCampUser(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        blank=True,
        null=True,
        default=None
    )
        
    first_name = models.CharField(
        max_length=150,
        blank=False,
        null=False
    )
    
    last_name = models.CharField(
        max_length=150,
        blank=False,
        null=False
    )
    
    phone_number = models.CharField(
        max_length=16
    )
    
    email = models.EmailField(
        unique=True,
        blank=False,
        null=False
    )
    
    def __str__(self):
        return self.email

class Enrollment(models.Model):
    name = models.CharField(
        max_length=128
    )

    enrollment_date = models.DateField(
        auto_now=True
    )

    enrollment_cancel_date = models.DateField(
        null=True,
        default=None
    )

    user = models.ForeignKey(
        BitCampUser,
        on_delete=models.CASCADE,
        related_name='enrollments',
        null=True
    )

    service_id = models.ForeignKey(
        content.Service,
        on_delete=models.SET_NULL,
        related_name='enrollments',
        null=True
    )

    program_id = models.ForeignKey(
        content.Program,
        on_delete=models.SET_NULL,
        related_name='enrollments',
        null=True
    )

    mentor_id = models.ForeignKey(
        content.Mentor,
        on_delete=models.SET_NULL,
        related_name='enrollments',
        null=True
    )

    status = models.CharField(
        max_length=16
    )
    
    start_payment = models.DateTimeField(
        null=False,
        blank=False
    )
    
    last_payment = models.DateTimeField(
        null=True,
        blank=False
    )

    payze_subscription_id = models.CharField(
        max_length=255, null=True, blank=True
    )

    payze_payment_url = models.URLField(
        max_length=255, null=True, blank=True
    )
    
    def __str__(self):
        return f"{self.service_id.title} | {self.user.email} | {self.user.phone_number} | {self.status}"
    
class KidsProfile(models.Model):
    user = models.ForeignKey(
        BitCampUser,
        on_delete=models.SET_NULL,
        related_name="kids_profiles",
        null=True
    )
    
    age = models.CharField(
        max_length=32
    )
    
    availability = models.CharField(
        max_length=64
    ) 

class Payment(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(
        verbose_name="Amount paid",
        max_digits=16,
        decimal_places=2,
        blank=False
    )
    status = models.CharField(
        max_length=128,
        verbose_name="Payment status"
    )
    payze_transactionId = models.CharField(
        max_length=128,
        verbose_name="Payze Transaction ID"
    )
    payze_paymentId = models.CharField(
        max_length=128,
        verbose_name="Payze Payment ID"
    )
    cardMask = models.CharField(
        max_length=32,
        verbose_name="Card Mask"
    )
    token = models.CharField(
        max_length=128,
        verbose_name="Token"
    )
    paymentUrl = models.URLField(
        verbose_name="Payment URL"
    )

    @cached_property
    def title(self):
        # Assuming each Payment object has a unique ID (primary key)
        return f"Payment: {self.id} | {self.amount} | {self.enrollment.user.email}"

    def __str__(self):
        return self.title
    