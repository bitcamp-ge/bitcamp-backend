# Generated by Django 4.2.5 on 2023-11-16 20:20

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DiscordUser',
            fields=[
                ('first_name', models.CharField(max_length=150)),
                ('last_name', models.CharField(max_length=150)),
                ('personal_id', models.CharField(max_length=32)),
                ('phone_number', models.CharField(max_length=32)),
                ('discord_id', models.CharField(max_length=18, primary_key=True, serialize=False, unique=True, verbose_name='Unique identifier for Discord user.')),
                ('onboarding_channel_id', models.CharField(max_length=18, unique=True, verbose_name='ID of the private Discord channel for onboarding.')),
                ('is_registered', models.BooleanField(default=False, verbose_name="Status of user's registration")),
            ],
        ),
    ]
