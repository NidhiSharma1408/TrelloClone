from django.db import models
from userauth.models import UserProfile
from cards.models import Card
# Create your models here.

class Checklist(models.Model):
    card = models.ForeignKey(Card,on_delete=models.CASCADE,related_name='checklists')
    name = models.CharField(default='Checklist',max_length=50)

class Task(models.Model):
    checklist = models.ForeignKey(Checklist,on_delete=models.CASCADE,related_name='tasks')
    name = models.CharField(max_length=50,null=False)
    completed = models.BooleanField(default=False)
