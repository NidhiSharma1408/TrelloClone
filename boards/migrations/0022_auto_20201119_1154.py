# Generated by Django 3.1.2 on 2020-11-19 06:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('boards', '0021_auto_20201118_2055'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='board',
            options={'ordering': ['team', '-id']},
        ),
    ]
