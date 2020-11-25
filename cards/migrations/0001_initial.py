# Generated by Django 3.1.2 on 2020-11-23 10:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('userauth', '0003_userprofile_bio'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attached_file',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='')),
            ],
        ),
        migrations.CreateModel(
            name='Attached_link',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('link', models.URLField()),
            ],
        ),
        migrations.CreateModel(
            name='Card',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=250)),
                ('desc', models.TextField(blank=True, null=True)),
                ('index', models.PositiveIntegerField()),
                ('due_date', models.DateTimeField(null=True)),
                ('complete', models.BooleanField(default=False)),
                ('archived', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['index', 'id'],
            },
        ),
        migrations.CreateModel(
            name='Label',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('color', models.CharField(max_length=6)),
                ('name', models.CharField(max_length=30)),
                ('card', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='label', to='cards.card')),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField()),
                ('created_at', models.DateTimeField(auto_now=True)),
                ('card', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='cards.card')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='userauth.userprofile')),
            ],
        ),
    ]
