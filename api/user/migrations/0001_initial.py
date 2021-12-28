# Generated by Django 4.0 on 2021-12-28 17:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=20, unique=True)),
                ('is_admin', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('last_update_password', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'db_table': 'user',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20, unique=True)),
            ],
            options={
                'db_table': 'membership',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Shopper',
            fields=[
                ('name', models.CharField(max_length=20)),
                ('nickname', models.CharField(max_length=20, unique=True)),
                ('email', models.EmailField(max_length=50)),
                ('phone', models.CharField(max_length=15, unique=True)),
                ('gender', models.BooleanField()),
                ('birthday', models.DateField()),
                ('height', models.IntegerField(null=True)),
                ('weight', models.IntegerField(null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.DO_NOTHING, parent_link=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'shopper',
                'managed': False,
            },
            bases=('user.user',),
        ),
        migrations.CreateModel(
            name='Wholesaler',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.DO_NOTHING, parent_link=True, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('name', models.CharField(max_length=60)),
                ('email', models.EmailField(max_length=50)),
                ('phone', models.CharField(max_length=15)),
            ],
            options={
                'db_table': 'wholesaler',
                'managed': False,
            },
            bases=('user.user',),
        ),
    ]
