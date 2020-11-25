# Generated by Django 3.1.2 on 2020-11-19 15:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('boards', '0022_auto_20201119_1154'),
    ]

    operations = [
        migrations.AddField(
            model_name='board',
            name='slug',
            field=models.SlugField(blank=True, max_length=250, null=True),
        ),
        migrations.AlterField(
            model_name='board',
            name='name',
            field=models.CharField(max_length=250),
        ),
        migrations.AlterField(
            model_name='card',
            name='name',
            field=models.CharField(max_length=250),
        ),
        migrations.AlterField(
            model_name='list',
            name='name',
            field=models.CharField(max_length=250),
        ),
    ]