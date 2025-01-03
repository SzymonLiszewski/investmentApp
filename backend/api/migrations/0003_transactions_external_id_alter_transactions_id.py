# Generated by Django 5.0.6 on 2024-08-14 18:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_alter_userstock_quantity'),
    ]

    operations = [
        migrations.AddField(
            model_name='transactions',
            name='external_id',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='transactions',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
    ]
