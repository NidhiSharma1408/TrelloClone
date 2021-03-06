# Generated by Django 3.1.2 on 2020-11-23 10:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('boards', '0025_auto_20201123_1325'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attached_link',
            name='card',
        ),
        migrations.RemoveField(
            model_name='card',
            name='list',
        ),
        migrations.RemoveField(
            model_name='card',
            name='members',
        ),
        migrations.RemoveField(
            model_name='card',
            name='voted_by',
        ),
        migrations.RemoveField(
            model_name='card',
            name='watched_by',
        ),
        migrations.RemoveField(
            model_name='checklist',
            name='card',
        ),
        migrations.RemoveField(
            model_name='comment',
            name='card',
        ),
        migrations.RemoveField(
            model_name='comment',
            name='user',
        ),
        migrations.RemoveField(
            model_name='label',
            name='card',
        ),
        migrations.RemoveField(
            model_name='list',
            name='board',
        ),
        migrations.RemoveField(
            model_name='list',
            name='watched_by',
        ),
        migrations.RemoveField(
            model_name='task',
            name='checklist',
        ),
        migrations.DeleteModel(
            name='Attached_file',
        ),
        migrations.DeleteModel(
            name='Attached_link',
        ),
        migrations.DeleteModel(
            name='Card',
        ),
        migrations.DeleteModel(
            name='Checklist',
        ),
        migrations.DeleteModel(
            name='Comment',
        ),
        migrations.DeleteModel(
            name='Label',
        ),
        migrations.DeleteModel(
            name='List',
        ),
        migrations.DeleteModel(
            name='Task',
        ),
    ]
