# Generated by Django 5.0.7 on 2025-02-03 15:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_type',
            field=models.CharField(choices=[('shipper', 'Yuk yuboruvchi'), ('passenger', "Yo'lovchi")], default='passenger', max_length=10),
        ),
    ]
