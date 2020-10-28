# Generated by Django 3.1.2 on 2020-10-28 07:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('boards', '0008_auto_20201027_1706'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='board',
            name='preference',
        ),
        migrations.AddField(
            model_name='preference',
            name='board',
            field=models.OneToOneField(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='pref', to='boards.board'),
            preserve_default=False,
        ),
    ]
