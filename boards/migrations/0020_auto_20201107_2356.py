# Generated by Django 3.1.2 on 2020-11-07 18:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('boards', '0019_auto_20201107_1813'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='card',
            options={'ordering': ['-priority']},
        ),
    ]
