# Generated by ChatGPT 3.5 on 2024-03-25 14:34

from django.db import migrations
from django.db.models import Max

def populate_last_payment_date(apps, schema_editor):
    Enrollment = apps.get_model('accounts', 'Enrollment')
    Payment = apps.get_model('accounts', 'Payment')
    
    for enrollment in Enrollment.objects.all():
        latest_payment = Payment.objects.filter(enrollment=enrollment).aggregate(max_date=Max('created_at'))
        last_payment_date = latest_payment.get('max_date')

        if last_payment_date:
            enrollment.last_payment = last_payment_date
            enrollment.save()
            
class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_enrollment_last_payment_enrollment_start_payment'),
    ]

    operations = [
        migrations.RunPython(populate_last_payment_date),
    ]