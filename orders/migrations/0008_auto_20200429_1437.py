# Generated by Django 2.2.12 on 2020-04-29 09:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_productpurchase'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productpurchase',
            name='user',
        ),
        migrations.AddField(
            model_name='productpurchase',
            name='order_id',
            field=models.CharField(default='abc123', editable=False, max_length=120),
            preserve_default=False,
        ),
    ]
