from django.db import models
from userauth.models import UserProfile
from lists.models import List
# Create your models here.


class Card(models.Model):
    name = models.CharField(max_length=250)
    desc = models.TextField(blank=True,null=True)
    index = models.PositiveIntegerField(blank=False)
    members = models.ManyToManyField(UserProfile,related_name='member_in_card')
    due_date = models.DateTimeField(null=True)
    complete = models.BooleanField(default=False)
    list = models.ForeignKey(List,on_delete=models.CASCADE,related_name='cards')
    archived = models.BooleanField(default=False)
    watched_by = models.ManyToManyField(UserProfile,related_name='watching_cards')
    voted_by = models.ManyToManyField(UserProfile,related_name='voted_cards')
    def __str__(self):
        return f'{self.id}-{self.name}-{self.list.id}-{self.list.board.id}'
    class Meta:
        ordering = ['index','id']

class Comment(models.Model):
    card = models.ForeignKey(Card,on_delete=models.CASCADE,related_name='comments')
    text = models.TextField(blank=False)
    user = models.ForeignKey(UserProfile,on_delete=models.CASCADE,related_name='comments')
    created_at = models.DateTimeField(auto_now=True)

class Attached_file(models.Model):
    card = models.ForeignKey(Card,on_delete=models.CASCADE,related_name='attached_files')
    file = models.FileField(null=False)

class Attached_link(models.Model):
    card = models.ForeignKey(Card,on_delete=models.CASCADE,related_name='attached_links')
    link = models.URLField(blank=False,null=False)

class Label(models.Model):
    color = models.CharField(max_length=6)
    name = models.CharField(max_length=30)
    card = models.ForeignKey(Card,on_delete=models.CASCADE,related_name='label')