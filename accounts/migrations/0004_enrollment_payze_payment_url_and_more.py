# Generated by Django 5.0.1 on 2024-01-11 22:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_alter_bitcampuser_first_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='enrollment',
            name='payze_payment_url',
            field=models.URLField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='enrollment',
            name='payze_subscription_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
