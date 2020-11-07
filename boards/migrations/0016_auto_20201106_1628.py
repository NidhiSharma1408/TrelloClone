# Generated by Django 3.1.2 on 2020-11-06 10:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('userauth', '0002_auto_20201101_1539'),
        ('boards', '0015_auto_20201102_1948'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='complete',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='attached_file',
            name='card',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attached_files', to='boards.card'),
        ),
        migrations.AlterField(
            model_name='card',
            name='members',
            field=models.ManyToManyField(related_name='member_in_card', to='userauth.UserProfile'),
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('card', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='boards.card')),
                ('voted_by', models.ManyToManyField(related_name='voted_cards', to='userauth.UserProfile')),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('card', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='boards.card')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='userauth.userprofile')),
            ],
        ),
    ]