# Generated by Django 4.0 on 2022-01-18 18:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0012_productimages'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='size',
            options={'managed': False, 'ordering': ['id']},
        ),
    ]
