# Generated by Django 5.0.7 on 2024-07-26 08:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oauth', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='useroauth',
            name='email',
            field=models.EmailField(default='tmp', max_length=254),
            preserve_default=False,
        ),
    ]
