# Generated by Django 4.0.2 on 2022-04-18 20:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0011_remove_refund_created_at_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderitem',
            name='cancellation_information',
        ),
        migrations.RemoveField(
            model_name='orderitem',
            name='exchange_information',
        ),
        migrations.RemoveField(
            model_name='orderitem',
            name='return_information',
        ),
    ]
