# Generated by Django 4.0.2 on 2022-04-26 16:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0016_alter_statushistory_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cancellationinformation',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='exchangeinformation',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='returninformation',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='statushistory',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
