# Generated by Django 3.1.2 on 2020-11-27 11:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('boards', '0027_delete_activity'),
        ('userauth', '0003_userprofile_bio'),
        ('lists', '0001_initial'),
        ('cards', '0002_auto_20201123_1552'),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('time_created', models.DateTimeField(auto_now_add=True)),
                ('board', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activity', to='boards.board')),
                ('card', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activity', to='cards.card')),
                ('list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activity', to='lists.list')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='activity', to='userauth.userprofile')),
            ],
        ),
    ]