# Generated by Django 4.0 on 2022-02-18 16:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0007_delete_productstyle'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subcategory',
            name='main_category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='subcategories', to='product.maincategory'),
        ),
    ]
